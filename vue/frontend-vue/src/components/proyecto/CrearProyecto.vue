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
          
          <div class="form-group mb-3">
            <label for="tipo_sector">Tipo de Sector:</label>
            <select v-model="tipo_industria" id="tipo_sector" class="form-control" required>
                <option v-for="tipo in tiposIndustria" :key="tipo" :value="tipo">
                    {{ tipo }}
                </option>
            </select>
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
// 🚨 URL LOCAL ASEGURADA
// const API_BASE_URL = 'http://127.0.0.1:8001'; 

export default {
    name: 'ModalProyecto', // Se usará este nombre ya que ModalProyecto.vue te manda a llamar a este.
    data() {
        return {
            isDark: false,
            nombre: '',
            descripcion: '',
            loading: false,
            error: null,
            usuarioId: null, 
            
            // 🚨 NUEVO ESTADO: Inicialización con un valor por defecto
            tipo_industria: 'Hogar Inteligente', 
            tiposIndustria: [
                'Hogar Inteligente',
                'Agricultura Precision',
                'Monitoreo Ambiental',
                'Industrial',
                'General',
            ],
        };
    },
    mounted() {
        // Cargar el ID del usuario logueado (necesario para el payload de creación)
        const resultado = JSON.parse(localStorage.getItem('resultado'));
        if (resultado && resultado.usuario) {
            this.usuarioId = resultado.usuario.id;
        } else {
            this.$router.push('/'); 
        }
        // Detección de tema
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            this.isDark = true;
        }
    },
    methods: {
        async submitProyecto() {
            if (!this.nombre || !this.descripcion || !this.usuarioId) {
                this.error = "Faltan datos de sesión o campos obligatorios.";
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
                        usuario_id: this.usuarioId,
                        // 🚨 CRÍTICO: Envío del nuevo campo
                        tipo_industria: this.tipo_industria 
                    })
                });

                const data = await response.json();

                if (!response.ok) {
                    throw new Error(data.message || data.detail || 'Fallo al crear el proyecto.');
                }
                
                // Éxito: Emitir evento para que MisProyectos.vue actualice su lista.
                this.$emit('creado', data.resultados[0]); 
                this.$emit('cerrar');

            } catch (err) {
                this.error = err.message || 'Error de conexión.';
            } finally {
                this.loading = false;
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
// $DARK-TEXT: #333333;
// $LIGHT-TEXT: #E4E6EB;
// $SUBTLE-BG-DARK: #2B2B40; 
// $SUBTLE-BG-LIGHT: #FFFFFF;
// $WHITE-SOFT: #F7F9FC;

// ----------------------------------------
// BASE DEL MODAL (POSICIONAMIENTO CRÍTICO)
// ----------------------------------------
.modal-base {
    position: fixed; top: 0; left: 0; width: 100%; height: 100%;
    background-color: rgba(0, 0, 0, 0.6);
    display: flex; justify-content: center; align-items: center;
    z-index: 9999;
}

.modal-contenido {
    width: 90%; max-width: 500px;
    border-radius: 15px; padding: 25px;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.4);
    transition: background-color 0.3s;
}

.modal-header {
    display: flex; justify-content: space-between; align-items: center;
    margin-bottom: 20px;
    h2 { font-size: 1.4rem; font-weight: 600; }
}

.btn-cerrar {
    background: none; border: none; font-size: 1.8rem; cursor: pointer; opacity: 0.7;
    &:hover { opacity: 1; }
}

// ----------------------------------------
// ESTILOS DE FORMULARIO
// ----------------------------------------
.form-group label {
    font-weight: 500;
    display: block;
    margin-bottom: 5px;
}
.alert-error {
    background-color: #f8d7da; color: #721c24; padding: 10px; border-radius: 5px; margin-bottom: 15px;
}
.btn-primary { background-color: $PRIMARY-PURPLE; border: none; } 
.btn-secondary { background-color: #6c757d; border: none; }

// ----------------------------------------
// TEMAS (DARK/LIGHT)
// ----------------------------------------
.theme-light { 
    background-color: $SUBTLE-BG-LIGHT; 
    color: $DARK-TEXT; 
    .form-control { border: 1px solid #ddd; }
}
.theme-dark { 
    background-color: $SUBTLE-BG-DARK; 
    color: $LIGHT-TEXT; 
    .form-control { 
        background-color: $BLUE-MIDNIGHT; 
        border: 1px solid rgba($LIGHT-TEXT, 0.2); 
        color: $LIGHT-TEXT; 
    }
    .btn-secondary { background-color: #444; color: $LIGHT-TEXT; }
}
</style>