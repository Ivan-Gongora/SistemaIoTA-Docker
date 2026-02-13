<template>
  <div class="modal-base" @click.self="$emit('close')">
    <div class="modal-contenido" :class="{ 'theme-dark': isDark, 'theme-light': !isDark }">
      
      <div class="modal-header">
        <h2>{{ modoEdicion ? 'Modificar Unidad' : 'Crear Nueva Unidad' }}</h2>
        <button @click="$emit('close')" class="btn-cerrar">&times;</button>
      </div>

      <div class="modal-body">
        <div v-if="error" class="alert-error">{{ error }}</div>
        
        <form @submit.prevent="submitUnidad">
          
          <div class="form-group mb-3">
            <label for="nombre">Nombre:</label>
            <input type="text" v-model="form.nombre" id="nombre" class="form-control" required>
          </div>
          
          <div class="form-group mb-3">
            <label for="simbolo">Símbolo (Ej: °C, %, V):</label>
            <input type="text" v-model="form.simbolo" id="simbolo" class="form-control" required maxlength="10">
          </div>
          <div class="form-group mb-3">
            <label for="magnitud_tipo">Tipo de Magnitud:</label>
            <input type="text" v-model="form.magnitud_tipo" id="magnitud_tipo" class="form-control" required placeholder="Ej: Temperatura, Presión">
            </div>
          
          <div class="form-group mb-4">
            <label for="descripcion">Descripción (Opcional):</label>
            <textarea v-model="form.descripcion" id="descripcion" class="form-control" rows="2"></textarea>
          </div>
          
          <div class="d-flex justify-content-end">
            <button type="button" @click="$emit('close')" class="btn btn-secondary me-2">Cancelar</button>
            <button type="submit" class="btn btn-primary" :disabled="loading">
              <i v-if="loading" class="bi bi-arrow-clockwise fa-spin"></i>
              {{ loading ? 'Guardando...' : (modoEdicion ? 'Guardar Cambios' : 'Crear Unidad') }}
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
    name: 'ModalUnidadMedida',
    props: {
        modoEdicion: { type: Boolean, default: false },
        unidadData: { type: Object, default: () => ({}) } // Datos para edición
    },
    data() {
        // Inicialización del formulario: copia datos para edición o usa valores vacíos
        const initialForm = this.modoEdicion && this.unidadData.id ? 
            { ...this.unidadData } : 
            { nombre: '', simbolo: '',magnitud_tipo: '', descripcion: null };

        return {
            isDark: false,
            loading: false,
            error: null,
            form: initialForm,
        };
    },
    mounted() {
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) { this.isDark = true; }
    },
    watch: {
        // Observador para reinicializar el formulario si cambia el proyecto a editar (en caso de reutilización)
        unidadData: {
            handler(newData) {
                if (this.modoEdicion) {
                    this.form = { ...newData };
                }
            },
            deep: true
        }
    },
    methods: {
        async submitUnidad() {
            if (!this.form.nombre || !this.form.simbolo) {
                this.error = "Nombre y Símbolo son obligatorios.";
                return;
            }
            
            this.loading = true;
            this.error = null;
            const token = localStorage.getItem('accessToken');
            
            const method = this.modoEdicion ? 'PUT' : 'POST';
            const id = this.unidadData.id;
            const url = `${API_BASE_URL}/api/unidades` + (this.modoEdicion ? `/${id}` : '');
            
            try {
                const response = await fetch(url, {
                    method: method,
                    headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
                    body: JSON.stringify(this.form)
                });

                const data = await response.json();

                if (!response.ok || data.status === 'error') {
                    throw new Error(data.detail || data.message || 'Fallo al guardar la unidad.');
                }
                
                // Éxito: Notifica al padre para recargar la lista
                this.$emit('unidad-guardada'); 
                this.$emit('close');

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
    width: 90%; max-width: 600px; /* Ancho para edición */
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
// TEMAS (DARK/LIGHT)
// ----------------------------------------
.theme-light { background-color: $SUBTLE-BG-LIGHT; color: $DARK-TEXT; }
.theme-dark { 
    background-color: $SUBTLE-BG-DARK; 
    color: $LIGHT-TEXT; 
    
    .form-control { /* Estilos para el input dentro del modal */
        background-color: $BLUE-MIDNIGHT; 
        border: 1px solid rgba($LIGHT-TEXT, 0.2); 
        color: $LIGHT-TEXT; 
    }
    .btn-secondary { /* Botón Cancelar */
        background-color: #444; 
        color: $LIGHT-TEXT; 
        border: none; 
    }
}
</style>