<template>
  <div class="modal-base" @click.self="$emit('close')">
    <div class="modal-contenido" :class="{ 'theme-dark': isDark, 'theme-light': !isDark }">
      
      <div class="modal-header">
        <h2>Modificar Sensor: {{ form.nombre || 'Cargando...' }}</h2>
        <button @click="$emit('close')" class="btn-cerrar">&times;</button>
      </div>

      <div class="modal-scroll-body">
        <div class="modal-body">
          <div v-if="error" class="alert-error mb-3">{{ error }}</div>
          
          <div v-if="loading" class="alert-info-mini mb-3">Cargando datos del sensor...</div>

          <form v-else @submit.prevent="submitSensor">
            
            <h4 class="section-heading mb-3">Datos del Sensor Principal</h4>
            
            <div class="alert-info-mini mb-3">
              <i class="bi bi-tablet-fill me-2"></i> En Dispositivo ID: <strong>{{ form.dispositivo_id || 'N/A' }}</strong>
            </div>

            <div class="form-row">
              <div class="form-group">
                <label for="nombre">Nombre del Sensor:</label>
                <input type="text" v-model="form.nombre" id="nombre" class="form-control" required placeholder="Ej: DHT22-Aire">
              </div>
              
              <div class="form-group">
                <label for="tipo">Tipo de Sensor:</label>
                <select v-model="tipoSeleccionado" id="tipo" class="form-control" required>
                  <option v-for="t in tiposSensor" :key="t" :value="t">{{ t }}</option>
                  <option value="Otro">Otro (Especifique)</option>
                </select>
              </div>
            </div>
            
            <div v-if="tipoSeleccionado === 'Otro'" class="form-group mb-3">
              <label for="otro_tipo">Especifique el Tipo:</label>
              <input type="text" v-model="form.tipo_otro" id="otro_tipo" class="form-control" required placeholder="Ej: Sensor de Temperatura Láser">
            </div>

            <div class="form-group mb-4">
              <label for="habilitado">Estado:</label>
              <select v-model="form.habilitado" id="habilitado" class="form-control" required>
                <option :value="true">Habilitado (Activo)</option>
                <option :value="false">Deshabilitado (Inactivo)</option>
              </select>
            </div>
            
            <p class="small-note text-muted">Nota: Los Campos de Medición se gestionan en la siguiente vista.</p>
          </form>
        </div>
      </div>
      
      <div class="modal-footer-actions">
          <button type="button" @click="$emit('close')" class="btn btn-secondary me-2">Cancelar</button>
          <button type="submit" @click="submitSensor" class="btn btn-primary" :disabled="loading">
            <i v-if="loading" class="bi bi-arrow-clockwise fa-spin"></i>
            {{ loading ? 'Guardando...' : 'Guardar Cambios' }}
          </button>
      </div>
    </div>
  </div>
</template>

<script>
// const API_BASE_URL = 'http://127.0.0.1:8001'; 

export default {
    name: 'ModalEditarSensor',
    props: {
        sensorId: { type: [Number, String], required: true } 
    },
    data() {
        return {
            isDark: false,
            loading: true, 
            error: null,
            tiposSensor: [
                'Digital (E/S)', 
                'Analógico (ADC)', 
                'Bus I2C/SPI', 
                'Serial/UART', 
                'Actuador (Relé/PWM)',
                'Otro' // El valor del option 'Otro' para el v-if
            ],
            
            tipoSeleccionado: '', 
            form: {
                id: null,
                nombre: '',
                tipo: '',
                habilitado: true,
                dispositivo_id: null,
                tipo_otro: '',
            },
        };
    },
    mounted() {
        this.loadSensorDetails();
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) { this.isDark = true; }
    },
    methods: {
        // -----------------------------------------------------
        // LÓGICA DE CARGA DE DATOS FRESCOS (GET)
        // -----------------------------------------------------
        async loadSensorDetails() {
            this.loading = true;
            this.error = null;
            const token = localStorage.getItem('accessToken');
            
            try {
                const response = await fetch(`${API_BASE_URL}/api/sensores/${this.sensorId}`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });

                if (!response.ok) {
                    throw new Error('No se pudo cargar la información del sensor.');
                }
                
                const data = await response.json();
                
                // Inicializar el formulario con los datos de la API
                this.form = {
                    id: data.id,
                    nombre: data.nombre,
                    tipo: data.tipo,
                    habilitado: data.habilitado === 1 || data.habilitado === true,
                    dispositivo_id: data.dispositivo_id, 
                    tipo_otro: '', // Siempre limpia al inicio
                };
                
                const tipoDB = data.tipo || '';

                // CORRECCIÓN 3: Lógica para identificar el tipo 'Otro'
                // Revisa si el valor de la DB NO está en la lista estándar
                if (this.tiposSensor.includes(tipoDB)) {
                    this.tipoSeleccionado = tipoDB; // Selecciona el valor estándar
                } else {
                    // Si es un valor personalizado (p. ej., "DHT22 (Temp/Hum)")
                    this.tipoSeleccionado = 'Otro'; // Forzamos el dropdown a 'Otro'
                    this.form.tipo_otro = tipoDB; // Guardamos el valor real para mostrarlo en el input
                }

            } catch (err) {
                this.error = err.message || 'Error de conexión.';
            } finally {
                this.loading = false;
            }
        },
       // -----------------------------------------------------
       // LÓGICA DE ENVÍO PUT
       // -----------------------------------------------------
        async submitSensor() {
            let finalType = '';
            
            // Determinar el valor final que se enviará a la DB
            if (this.tipoSeleccionado === 'Otro') {
                if (!this.form.tipo_otro.trim()) {
                    this.error = "Por favor, especifique el tipo de sensor.";
                    return;
                }
                finalType = this.form.tipo_otro.trim();
            } else {
                finalType = this.tipoSeleccionado;
            }

            if (!this.form.nombre || !finalType) {
                this.error = "El nombre y tipo son obligatorios.";
                return;
            }
            
            this.loading = true;
            this.error = null;
            const token = localStorage.getItem('accessToken');
            
            try {
                const payload = {
                    nombre: this.form.nombre,
                    tipo: finalType, // Usamos el valor final
                    habilitado: this.form.habilitado
                };
                
                const response = await fetch(`${API_BASE_URL}/api/sensores/${this.form.id}`, {
                    method: 'PUT',
                    headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });

                const data = await response.json();

                if (!response.ok) {
                    throw new Error(data.message || data.detail || 'Fallo al actualizar el sensor.');
                    
                }
                
                // CORRECCIÓN 4: Cerrar el modal SOLAMENTE si la API fue exitosa
                this.$emit('sensor-actualizado', data.resultados[0]);
                this.$emit('close'); 

            } catch (err) {
                this.error = err.message || 'Error de conexión.';
            } finally {
                this.loading = false;
            }
        },
        // -----------------------------------------------------
        // MÉTODOS AUXILIARES DE TEMA (Mantener el original)
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
    max-width: 650px; /* Ancho cómodo para el mapa */
    border-radius: 15px; 
    padding: 0; /* 🚨 CRÍTICO: El padding se mueve a header/footer/scroll-body */
    max-height: 90vh; /* 🚨 CRÍTICO: Altura máxima de la ventana */
    display: flex;
    flex-direction: column;
    overflow: hidden; /* Evita que el scroll afecte al contenedor principal */
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.4);
    transition: background-color 0.3s;
}
.modal-contenido-lg { 
    max-width: 800px; /* 🚨 Hacemos el modal más grande para los campos dinámicos */
    /* ... otros estilos ... */
}
.modal-header {
    display: flex; justify-content: space-between; align-items: center;
    padding: 20px 25px; /* Padding Fijo */
    flex-shrink: 0; /* Evita que el header se encoja */
    border-bottom: 1px solid rgba($GRAY-COLD, 0.1);
    h2 { font-size: 1.4rem; font-weight: 600; }
}
.btn-cerrar {
background: none; border: none; font-size: 1.8rem; cursor: pointer; opacity: 0.7;
 &:hover { opacity: 1; }
}
.modal-body {
    padding: 15px 25px; 
}
.form-row { display: flex; gap: 20px; margin-bottom: 15px; }
.form-group { flex: 1; margin-bottom: 15px; }
.form-group label { font-weight: 500; display: block; margin-bottom: 5px; }
.badge {
    background-color: #8A2BE2; color: white; padding: 3px 8px; border-radius: 50px; font-size: 0.8rem;
}
.btn-add-campo { background-color: #555; color: white; }
/* 🚨 ESTILOS DINÁMICOS DE CAMPOS */
.campo-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px;
    margin-bottom: 10px;
    border: 1px solid #ddd;
    border-radius: 8px;
    
    .campo-details {
        display: flex;
        align-items: center;
        flex-grow: 1;
    }
    .campo-index {
        font-weight: 600;
        margin-right: 15px;
        min-width: 70px;
    }
    .form-control-sm {
        padding: 5px 10px;
        font-size: 0.9rem;
        width: 150px;
    }
    .btn-remove-campo {
        color: #e74c3c;
        background: none;
        border: none;
        cursor: pointer;
        font-size: 1.2rem;
    }
}
.section-heading {
    font-size: 1.1rem;
    font-weight: 600;
    margin-bottom: 15px;
    padding-bottom: 5px;
    border-bottom: 1px solid rgba($GRAY-COLD, 0.2);
}

.alert-info-mini {
    padding: 10px;
    border-radius: 8px;
    background-color: rgba($PRIMARY-PURPLE, 0.1);
    color: $PRIMARY-PURPLE;
    font-size: 0.9rem;
}

/* TEMAS */
.theme-light { 
    background-color: $SUBTLE-BG-LIGHT; color: $DARK-TEXT; 
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
    .section-heading { border-bottom-color: rgba($LIGHT-TEXT, 0.2); }
}
</style>