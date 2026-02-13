<template>
  <div class="modal-base" @click.self="$emit('cerrar')">
    <div class="modal-contenido" :class="{ 'theme-dark': isDark }">
      <div class="modal-header">
        <h2>Crear Nuevo Proyecto IoT</h2>
        <button @click="$emit('cerrar')" class="btn-cerrar">&times;</button>
      </div>

      <div class="modal-body">
        <div v-if="error" class="alert-error">{{ error }}</div>
        
        <form @submit.prevent="submitProyecto">
          <div class="form-group mb-3">
            <label for="nombre">Nombre del Proyecto:</label>
            <input type="text" v-model="nombre" id="nombre" class="form-control" required />
          </div>
          
          <div class="form-group mb-4">
            <label for="descripcion">Descripción:</label>
            <textarea v-model="descripcion" id="descripcion" class="form-control" rows="3" required></textarea>
          </div>
          
          <div class="d-flex justify-content-end">
            <button type="button" @click="$emit('cerrar')" class="btn btn-secondary me-2">Cancelar</button>
            <button type="submit" class="btn btn-primary" :disabled="loading">
              <i v-if="loading" class="bi bi-arrow-clockwise fa-spin"></i>
              {{ loading ? 'Creando...' : 'Crear Proyecto' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
// const API_BASE_URL = 'http://127.0.0.1:8001';


export default {
    name: 'ModalProyecto',
    props: {
        proyecto: {
            type: Object,
            required: true
        },
        // 1. AÑADIR ESTA PROP (igual que en TarjetaDispositivo)
        isDark: {
            type: Boolean,
            required: true
        }
    },
    data() {
        return {
            nombre: '',
            descripcion: '',
            loading: false,
            error: null,
            usuarioId: null,
        };
    },
    mounted() {
        // Cargar el ID del usuario logueado y el tema
        const resultado = JSON.parse(localStorage.getItem('resultado'));
        if (resultado && resultado.usuario) {
            this.usuarioId = resultado.usuario.id;
        } else {
            this.$router.push('/'); // Redirigir si no hay sesión
        }
        this.detectarTemaSistema();
    },
    methods: {
        async submitProyecto() {
            if (!this.nombre || !this.descripcion) {
                this.error = "Todos los campos son obligatorios.";
                return;
            }
            
            this.loading = true;
            this.error = null;
            const token = localStorage.getItem('accessToken');
            
            try {
                const response = await fetch(`${API_BASE_URL}/api/crear_proyecto/`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        nombre: this.nombre,
                        descripcion: this.descripcion,
                        usuario_id: this.usuarioId // ID del creador
                    })
                });

                const data = await response.json();

                if (!response.ok) {
                    throw new Error(data.message || data.detail || 'Fallo al crear el proyecto.');
                }

                // Éxito: Emitir evento para que el componente MisProyectos actualice su lista
                this.$emit('creado', data.resultados[0]);
                this.$emit('cerrar');

            } catch (err) {
                this.error = err.message || 'Error de conexión.';
            } finally {
                this.loading = false;
            }
        },
        detectarTemaSistema() {
            if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
                this.isDark = true;
            }
        },
    }
};
</script>
<style scoped lang="scss">
// ----------------------------------------
// VARIABLES DE LA PALETA
// ----------------------------------------
// $PRIMARY-PURPLE: #8A2BE2;
// $SUCCESS-COLOR: #1ABC9C;
// $BLUE-MIDNIGHT: #1A1A2E;
// $LIGHT-TEXT: #E4E6EB;
// $DARK-TEXT: #333333;
// $SUBTLE-BG-DARK: #2B2B40; 
// $SUBTLE-BG-LIGHT: #FFFFFF;
// $LIGHT-TEXT: #E4E6EB;     // También es necesaria
// $WHITE-SOFT: #F7F9FC;     // 🚨 Esta es la variable que faltaba

// ----------------------------------------
// BASE DEL MODAL
// ----------------------------------------
.modal-compartir {
    position: fixed; top: 0; left: 0; width: 100%; height: 100%;
    background-color: rgba(0, 0, 0, 0.6);
    display: flex; justify-content: center; align-items: center;
    z-index: 9999;
}

.modal-contenido {
    width: 90%; max-width: 550px;
    border-radius: 15px; padding: 25px;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.4);
    transition: background-color 0.3s;
}

.modal-header {
    display: flex; justify-content: space-between; align-items: center;
    margin-bottom: 20px;
    h2 { font-size: 1.5rem; }
}

.btn-cerrar {
    background: none; border: none; font-size: 1.8rem; cursor: pointer;
    opacity: 0.7; transition: opacity 0.2s;
    &:hover { opacity: 1; }
}

// ----------------------------------------
// ESTILOS DE CONTENIDO
// ----------------------------------------

.link-generation-section {
    margin-bottom: 30px;
    h3 { font-size: 1.1rem; margin-bottom: 10px; font-weight: 600; }
}

.link-box {
    display: flex; gap: 10px;
    .form-control {
        flex-grow: 1; padding: 10px; border-radius: 8px; border: 1px solid;
        font-size: 0.9rem; background-color: rgba($PRIMARY-PURPLE, 0.05);
        cursor: text;
    }
    .btn-copy {
        background-color: $PRIMARY-PURPLE; color: white; border: none;
        padding: 10px 15px; border-radius: 8px; cursor: pointer;
        transition: background-color 0.2s;
        &:disabled { opacity: 0.5; cursor: not-allowed; }
        i { font-size: 1.1rem; }
    }
}

.link-status {
    font-size: 0.85rem; margin-top: 10px; color: $SUCCESS-COLOR;
}

.user-management-section {
    h4 { font-size: 1.1rem; margin-bottom: 15px; border-bottom: 1px solid; padding-bottom: 5px; }
}
.user-list {
    list-style: none; 
    padding: 0;
    
    .user-item {
        display: flex; 
        align-items: center;
        padding: 10px 15px; 
        margin-bottom: 5px;
        border-radius: 8px;
        transition: background-color 0.2s;
        
        // 🚨 ÍCONOS Y TEXTO
        i { margin-right: 10px; color: $PRIMARY-PURPLE; font-size: 1.1rem; }
        .member-name { font-weight: 600; margin-right: 5px; }
        .member-role { font-size: 0.9rem; opacity: 0.7; }

        // 🚨 PROPIETARIO (Estilo de distinción)
        &.owner { 
            background-color: rgba($SUCCESS-COLOR, 0.1); 
            border-left: 3px solid $SUCCESS-COLOR;
            padding-left: 12px;
        }
    }
    
    // 🚨 Botón de Remover (La X)
    .btn-remove {
        margin-left: auto; /* Mueve el botón al extremo derecho */
        background: none; 
        border: none; 
        color: #ff6347; /* Color de peligro */
        cursor: pointer; 
        opacity: 0.7;
        padding: 5px;

        &:hover { 
            opacity: 1; 
            color: #ff0000;
        }
    }
}

// ----------------------------------------
// TEMAS (DARK/LIGHT)
// ----------------------------------------
// TEMAS (Asegurar el contraste del botón de remover en modo oscuro)
.theme-dark {
    // ...
    .user-item {
        color: $LIGHT-TEXT;
        &:hover {
            background-color: rgba($LIGHT-TEXT, 0.05);
        }
    }
    .user-list .btn-remove {
        color: #ff6347;
    }
}
// MODO OSCURO
.theme-dark {
    background-color: $SUBTLE-BG-DARK;
    color: $LIGHT-TEXT;
    
    .btn-cerrar { color: $LIGHT-TEXT; }
    .form-control {
        background-color: $BLUE-MIDNIGHT;
        color: $LIGHT-TEXT;
        border-color: rgba($LIGHT-TEXT, 0.2);
    }
    .user-management-section h4 { border-bottom-color: rgba($LIGHT-TEXT, 0.3); }
}

// MODO CLARO
.theme-light {
    background-color: $SUBTLE-BG-LIGHT;
    color: $DARK-TEXT;
    
    .btn-cerrar { color: $DARK-TEXT; }
    .form-control {
        background-color: $WHITE-SOFT;
        color: $DARK-TEXT;
        border-color: #ddd;
    }
    .user-management-section h4 { border-bottom-color: #ddd; }
}
</style>