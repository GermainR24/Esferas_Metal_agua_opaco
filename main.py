from glApp.PyOGApp import *
from glApp.Utils import *
from glApp.Axes import *
from glApp.LoadMesh import *


vertex_shader = r'''
#version 330 core

in vec3 position;
in vec3 vertex_color;
in vec3 vertex_normal;
in vec2 vertex_uv;

uniform mat4 projection_mat;
uniform mat4 model_mat;
uniform mat4 view_mat;

out vec3 frag_color;
out vec3 frag_normal;
out vec3 frag_pos;
out vec3 light_pos;
out vec2 frag_uv;

void main()
{
    // Posición de la luz = posición de la cámara (como antes)
    light_pos = vec3(inverse(model_mat) * 
                     vec4(view_mat[3][0], view_mat[3][1], view_mat[3][2], 1.0));

    gl_Position = projection_mat * inverse(view_mat) * model_mat * vec4(position, 1.0);

    frag_normal = mat3(transpose(inverse(model_mat))) * vertex_normal;  // Normal transformada correctamente
    frag_pos = vec3(model_mat * vec4(position, 1.0));
    frag_color = vertex_color;
    frag_uv = vertex_uv;
}
'''

fragment_shader_metal_agua_opaco = r'''
#version 330 core
in vec3 frag_normal;
in vec3 frag_pos;
in vec2 frag_uv;

out vec4 final_color;

uniform vec3 view_pos;
uniform vec3 light_pos;
uniform sampler2D tex_sampler;
uniform int material_type; // 0 = metal, 1 = agua, 2 = opaco

void main()
{
    vec3 norm = normalize(frag_normal);
    vec3 light_dir = normalize(light_pos - frag_pos);
    vec3 view_dir = normalize(view_pos - frag_pos);
    vec3 halfway_dir = normalize(light_dir + view_dir);

    vec3 tex_color = texture(tex_sampler, frag_uv).rgb;
    vec3 light_color = vec3(1.0, 1.0, 1.0);

    vec3 material_base;
    float ambient_strength;
    float specular_strength;
    int shininess;
    vec3 base_color;

    if(material_type == 0){
        // Metal
        material_base = vec3(0.7, 0.7, 0.7); //color gris
        ambient_strength = 0.44;
        specular_strength = 0.77;
        shininess = 17;
        base_color = tex_color;

    } else if(material_type == 1){
        // Agua
        material_base = vec3(0.2, 0.5, 0.8); //color azul
        ambient_strength = 0.4;
        specular_strength = 1.0;
        shininess = 64;
        base_color = mix(tex_color, tex_color * material_base, 0.3);

    } else {
        // Opaco
        material_base = vec3(1.0, 1.0, 1.0);
        ambient_strength = 0.3;
        specular_strength = 0.0;
        shininess = 16;
        base_color = tex_color;
    }


    // 1. Luz ambiental
    vec3 ambient = ambient_strength * material_base * light_color;

    // 2. Luz difusa (Lambert)
    float diff = max(dot(norm, light_dir), 0.0);
    vec3 diffuse = diff * light_color;

    // 3. Luz especular (Blinn)
    float spec = pow(max(dot(norm, halfway_dir), 0.0), shininess);
    vec3 specular = specular_strength * spec * light_color;

    // Color final
    vec3 result = (ambient + diffuse) * base_color + specular;
    final_color = vec4(result, 1.0);
}

'''
def load_texture(filename):
    texture_surface = pygame.image.load(filename)
    texture_data = pygame.image.tostring(texture_surface, "RGB", 1)
    width = texture_surface.get_width()
    height = texture_surface.get_height()

    texture_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, texture_id)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, width, height, 0, GL_RGB, GL_UNSIGNED_BYTE, texture_data)

    return texture_id

class ShaderObjects(PyOGApp):

    def __init__(self):
        super().__init__(850, 200, 1000, 800)
        self.axes = None
        self.moving_cube = None
        self.teapot1 = None
        self.teapot2 = None
        self.esfera= None


    def initialise(self):
        self.program_id = create_program(vertex_shader, fragment_shader_metal_agua_opaco)

        # texturas
        self.texture_id_metal = load_texture("texturas/metal.png")
        self.texture_id_agua = load_texture("texturas/agua.png")
        self.texture_id_opaco = load_texture("texturas/opaco.png")

        # crear esferas
        self.esfera_metal = LoadMesh("models/esfera.obj", self.program_id,
                        location=pygame.Vector3(-2, 0, -2),
                        scale=pygame.Vector3(0.5, 0.5, 0.5),
                        move_rotation=Rotation(1, pygame.Vector3(0, 1, 0)))

        self.esfera_agua = LoadMesh("models/esfera.obj", self.program_id,
                                location=pygame.Vector3(0, 0, -2),
                                scale=pygame.Vector3(0.5, 0.5, 0.5),
                                move_rotation=Rotation(1, pygame.Vector3(0, 1, 0)))

        self.esfera_opaco = LoadMesh("models/esfera.obj", self.program_id,
                                location=pygame.Vector3(2, 0, -2),
                                scale=pygame.Vector3(0.5, 0.5, 0.5),
                                move_rotation=Rotation(1, pygame.Vector3(0, 1, 0)))


        self.camera = Camera(self.program_id, self.screen_width, self.screen_height)
        glEnable(GL_DEPTH_TEST)

    def camera_init(self):
        pass

    def display(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glUseProgram(self.program_id)
        self.camera.update()
        glActiveTexture(GL_TEXTURE0)
        
        # esfera metal
        glBindTexture(GL_TEXTURE_2D, self.texture_id_metal)
        glUniform1i(glGetUniformLocation(self.program_id, "material_type"), 0)
        self.esfera_metal.draw()

        # esfera agua
        glBindTexture(GL_TEXTURE_2D, self.texture_id_agua)
        glUniform1i(glGetUniformLocation(self.program_id, "material_type"), 1)
        self.esfera_agua.draw()

        # esfera opaco
        glBindTexture(GL_TEXTURE_2D, self.texture_id_opaco)
        glUniform1i(glGetUniformLocation(self.program_id, "material_type"), 2)
        self.esfera_opaco.draw()



ShaderObjects().mainloop()
