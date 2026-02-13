<template>
  <div class="modal-base" @click.self="$emit('close')">
    <div class="modal-contenido" :class="{ 'theme-dark': isDark, 'theme-light': !isDark }">
      
      <div class="modal-header">
        <h2>{{ modoEdicion ? 'Modificar Campo' : 'Crear Nuevo Campo' }}</h2>
        <button @click="$emit('close')" class="btn-cerrar">&times;</button>
      </div>

      <div class="modal-body">
        <div v-if="error" class="alert-error mb-3">{{ error }}</div>
        <div v-if="loadingUnidades" class="alert-info-mini mb-3">Cargando unidades de medida...</div>
        
        <form @submit.prevent="submitCampo">
          
          <div class="alert-info-mini mb-3">
             <i class="bi bi-cpu-fill me-2"></i> Asignando a Sensor ID: <strong>{{ sensorId }}</strong>
          </div>

          <div class="form-group mb-3">
            <label for="nombre">Nombre del Campo:</label>
            <input type="text" v-model="form.nombre" id="nombre" class="form-control" required placeholder="Ej: Temperatura Ambiente">
          </div>
          
          <div class="form-row">
            <div class="form-group">
              <label for="tipo_valor">Tipo de Dato (DB):</label>
              <select v-model="form.tipo_valor" id="tipo_valor" class="form-control" required>
                  <option value="Float">Flotante (Decimal)</option>
                  <option value="Int">Entero</option>
                  <option value="String">Texto (String)</option>
              </select>
            </div>
            
            <div class="form-group">
              <label for="unidad">Unidad de Medida:</label>
              <select v-model="form.unidad_medida_id" id="unidad" class="form-control" required>
                  <option :value="null" disabled>Seleccionar Unidad (Ej: °C, %)</option>
                  <option v-for="unidad in unidadesMedida" :key="unidad.id" :value="unidad.id">
                      {{ unidad.nombre }} ({{ unidad.simbolo }})
                  </option>
              </select>
            </div>
          </div>
          
          <div class="d-flex justify-content-end mt-4">
            <button type="button" @click="$emit('close')" class="btn btn-secondary me-2">Cancelar</button>
            <button type="submit" class="btn btn-primary" :disabled="loading || loadingUnidades">
              <i v-if="loading" class="bi bi-arrow-clockwise fa-spin"></i>
              {{ modoEdicion ? 'Guardar Cambios' : 'Crear Campo' }}
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
    name: 'ModalCampoSensor',
    props: {
        modoEdicion: { type: Boolean, default: false },
        sensorId: { type: [Number, String], required: true },
        // 'campoData' se usaría para el modo edición
        campoData: { type: Object, default: () => ({}) } 
    },
    data() {
        return {
            isDark: false, 
            loading: false, 
            loadingUnidades: true,
            error: null,
            unidadesMedida: [], // Almacena la lista de unidades de la API
            
            form: {
                nombre: '',
                tipo_valor: 'Float',
                unidad_medida_id: null,
                sensor_id: parseInt(this.sensorId),
            },
        };
    },
    mounted() {
        this.detectarTemaSistema();
        this.loadUnidades();

        // Si estamos en modo Edición, poblamos el formulario
        if (this.modoEdicion && this.campoData) {
            this.form = { ...this.campoData };
        }
    },
    methods: {
        // -----------------------------------------------------
        // CARGA DE DATOS (UNIDADES)
        // -----------------------------------------------------
        async loadUnidades() {
            this.loadingUnidades = true;
            const token = localStorage.getItem('accessToken');
            try {
                const response = await fetch(`${API_BASE_URL}/api/unidades`, { 
                    headers: { 'Authorization': `Bearer ${token}` } 
                });
                if (!response.ok) {
                    throw new Error('Fallo al cargar unidades de medida. Verifique permisos.');
                }
                this.unidadesMedida = await response.json();
            } catch (err) {
                this.error = 'No se pudo cargar la lista de unidades.';
                console.error("Error cargando unidades:", err);
            } finally {
                this.loadingUnidades = false;
            }
        },
        
        // -----------------------------------------------------
        // LÓGICA DE ENVÍO (POST/PUT)
        // -----------------------------------------------------
        async submitCampo() {
            if (!this.form.nombre || !this.form.unidad_medida_id) {
                this.error = "Debe asignar un nombre y una unidad de medida.";
                return;
            }
            
            this.loading = true;
            this.error = null;
            const token = localStorage.getItem('accessToken');
            
            // Determinar la URL y el método (POST para crear, PUT para modificar)
            let url = `${API_BASE_URL}/api/campos_sensores/`;
            let method = 'POST';
            
            if (this.modoEdicion) {
                url = `${API_BASE_URL}/api/campos_sensores/${this.campoData.id}`;
                method = 'PUT';
            }
            
            try {
                const response = await fetch(url, {
                    method: method,
                    headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
                    body: JSON.stringify(this.form)
                });

                const data = await response.json();

                if (!response.ok) {
                    throw new Error(data.detail || data.message || 'Fallo en la operación del campo.');
                }
                
                this.$emit('campo-guardado');
                this.$emit('close');

            } catch (err) {
                this.error = err.message || 'Error de conexión.';
            } finally {
                this.loading = false;
            }
        },

        // -----------------------------------------------------
        // MÉTODOS AUXILIARES DE TEMA
        // -----------------------------------------------------
        handleThemeChange(event) { this.isDark = event.matches; },
        detectarTemaSistema() {
            if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
                this.isDark = true;
            } else {
                this.isDark = false;
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
// $GRAY-COLD: #99A2AD;

// ----------------------------------------
// ESTILOS DEL MODAL (Copiado de Modales Anteriores)
// ----------------------------------------
.modal-base {
    position: fixed; top: 0; left: 0; width: 100%; height: 100%;
    background-color: rgba(0, 0, 0, 0.6);
    display: flex; justify-content: center; align-items: center;
    z-index: 9999;
}

.modal-contenido {
    width: 90%; 
    max-width: 550px; /* Tamaño estándar para formularios simples */
    border-radius: 15px; 
    padding: 0; 
    max-height: 90vh; 
    display: flex;
    flex-direction: column;
    overflow: hidden;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.4);
    transition: background-color 0.3s;
}
.modal-header {
    display: flex; justify-content: space-between; align-items: center;
    padding: 20px 25px; 
    flex-shrink: 0;
    border-bottom: 1px solid rgba($GRAY-COLD, 0.1);
    h2 { font-size: 1.4rem; font-weight: 600; }
}
.btn-cerrar {
    background: none; border: none; font-size: 1.8rem; cursor: pointer; opacity: 0.7;
    &:hover { opacity: 1; }
}
.modal-body {
    padding: 20px 25px; 
    overflow-y: auto;
}
.form-row { display: flex; gap: 20px; }
.form-group { flex: 1; margin-bottom: 15px; }
.form-group label { font-weight: 500; display: block; margin-bottom: 5px; }

.modal-footer-actions {
    flex-shrink: 0; 
    padding: 15px 25px; 
    border-top: 1px solid rgba(0, 0, 0, 0.1);
    background-color: inherit; 
    display: flex;
    justify-content: flex-end;
    gap: 10px;
}

.alert-info-mini {
    padding: 10px;
    border-radius: 8px;
    background-color: rgba($PRIMARY-PURPLE, 0.1);
    color: $PRIMARY-PURPLE;
    font-size: 0.9rem;
}
.alert-error {
    background-color: #f8d7da; color: #721c24; padding: 10px; border-radius: 5px;
}

/* TEMAS */
.theme-light { 
    background-color: $SUBTLE-BG_LIGHT; color: $DARK-TEXT; 
    .form-control { border: 1px solid #ddd; }
    .modal-header, .modal-footer-actions { border-color: #ddd; }
}
.theme-dark { 
    background-color: $SUBTLE-BG-DARK; 
    color: $LIGHT-TEXT; 
    .modal-header, .modal-footer-actions { border-color: rgba($LIGHT-TEXT, 0.2); }
    .form-control { 
        background-color: $BLUE-MIDNIGHT; 
        border: 1px solid rgba($LIGHT-TEXT, 0.2); 
        color: $LIGHT-TEXT; 
    }
    .btn-secondary { background-color: #444; color: $LIGHT-TEXT; }
}
</style>