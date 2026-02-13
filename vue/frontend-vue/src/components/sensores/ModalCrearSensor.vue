<template>
  <div class="modal-base" @click.self="$emit('close')">
    <div class="modal-contenido-lg" :class="{ 'theme-dark': isDark }">
      
      <div class="modal-header">
        <h2>Registrar Nuevo Sensor</h2>
        <button @click="$emit('close')" class="btn-cerrar">&times;</button>
      </div>

      <div class="modal-scroll-body">
        <div class="modal-body">
          <div v-if="error" class="alert-error mb-3">{{ error }}</div>
          
          <form @submit.prevent="submitSensor">
            
            <h4 class="section-heading mb-3">Datos del Sensor Principal</h4>
            
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
              <input type="text" v-model="form.tipo" id="otro_tipo" class="form-control" required placeholder="Ej: Sensor de Temperatura Láser">
            </div>

            <div class="form-group mb-4">
              <label for="habilitado">Estado Inicial:</label>
              <select v-model="form.habilitado" id="habilitado" class="form-control" required>
                  <option :value="true">Habilitado (Activo)</option>
                  <option :value="false">Deshabilitado (Inactivo)</option>
              </select>
              <p class="small-note">La fecha de creación será asignada automáticamente.</p>
            </div>
            
            <h4 class="section-heading mt-4">Campos de Medición  <span class="badge">{{ form.campos.length }}</span></h4>

            <div v-if="form.campos.length === 0" class="alert-warning-mini">
                 <i class="bi bi-info-circle-fill"></i> Un sensor debe tener al menos un campo de medición.
            </div>

            <div v-for="(campo, index) in form.campos" :key="index" class="campo-item">
                <div class="campo-details">
                    <p class="campo-index">Campo {{ index + 1 }}</p>
                    <input type="text" v-model="campo.nombre" placeholder="Nombre (Ej: Temperatura Ambiente)" class="form-control-sm me-2" required>
                    
                    <select v-model="campo.tipo_valor" class="form-control-sm me-2" required>
                        <option value="Float">Flotante (Decimal)</option>
                        <option value="Int">Entero</option>
                        <option value="String">Texto (String)</option>
                    </select>

                    <select v-model="campo.unidad_medida_id" class="form-control-sm me-2" required>
                        <option :value="null" disabled>Seleccionar Unidad</option>
                        <option v-for="unidad in unidadesMedida" :key="unidad.id" :value="unidad.id">
                            {{ unidad.nombre }} ({{ unidad.simbolo }})
                        </option>
                    </select>
                </div>
                <button @click.prevent="removeCampo(index)" class="btn-remove-campo" title="Eliminar campo">
                    <i class="bi bi-trash-fill"></i>
                </button>
            </div>
            
            <button @click.prevent="addCampo" type="button" class="btn btn-add-campo mt-3">
                <i class="bi bi-node-plus"></i> Añadir Campo de Medición
            </button>
          </form>
        </div>
      </div>
      
      <div class="modal-footer-actions">
            <button type="button" @click="$emit('close')" class="btn btn-secondary me-2">Cancelar</button>
            <button type="submit" @click="submitSensor" class="btn btn-primary" :disabled="loading || form.campos.length === 0">
              <i v-if="loading" class="bi bi-arrow-clockwise fa-spin"></i>
              {{ loading ? 'Guardando...' : 'Guardar Sensor' }}
            </button>
      </div>
    </div>
  </div>
</template>
<script>
// const API_BASE_URL = 'http://127.0.0.1:8001';

export default {
    name: 'ModalCrearSensor',
    props: {
        dispositivoId: {
            type: [Number, String],
            required: true
        }
    },
    data() {
        return {
            isDark: false,
            loading: false,
            error: null,
            // ModalCrearSensor.vue <script> (dentro de data())
            tiposSensor: [
                'Digital (E/S)',
                'Analógico (ADC)',
                'Bus I2C/SPI',
                'Serial/UART',
                'Actuador (Relé/PWM)',
                'General' 
            ],
            unidadesMedida: [], // 🚨 Lista de unidades de medida de la API
            
            tipoSeleccionado: 'Digital (E/S)', 
            
            form: {
                dispositivo_id: parseInt(this.dispositivoId), // 🚨 Esto ya es un entero
                nombre: '',
                tipo: 'DHT22 (Temp/Hum)', 
                habilitado: true,
                campos: [], // 🚨 CRÍTICO: Array para campos de medición
            }
        };
    },
    watch: {
        tipoSeleccionado(newValue) {
            this.form.tipo = (newValue !== 'Otro') ? newValue : ''; 
        },
    },
    mounted() {
this.loadUnidades();        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) { this.isDark = true; }
    },
    methods: {
        // -----------------------------------------------------
        // 🚨 FUNCIÓN CRÍTICA: CONSUMO DE UNIDADES DE MEDIDA
        // -----------------------------------------------------
        async loadUnidades() {
            const token = localStorage.getItem('accessToken');
            try {
                const response = await fetch(`${API_BASE_URL}/api/unidades`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (!response.ok) {
                    throw new Error('Fallo al cargar unidades de medida.');
                }
                this.unidadesMedida = await response.json();
            } catch (err) {
                console.error("Error cargando unidades:", err);
                this.error = 'No se pudo cargar las unidades de medida.';
            }
        },

        // -----------------------------------------------------
        // GESTIÓN DINÁMICA DE CAMPOS
        // -----------------------------------------------------
        addCampo() {
            this.form.campos.push({
                nombre: '',
                tipo_valor: 'Float',
                unidad_medida_id: null, // Debe ser null para forzar la selección
                sensor_id: 0,
            });
        },
        removeCampo(index) {
            this.form.campos.splice(index, 1);
        },

        // -----------------------------------------------------
        // ENVÍO PRINCIPAL DEL SENSOR (INCLUYE CAMPOS)
        // -----------------------------------------------------
       // ModalCrearSensor.vue <script> (dentro de methods)

async submitSensor() {
    // 1. Validaciones de Frontend
    if (this.tipoSeleccionado === 'Otro' && !this.form.tipo) {
        this.error = "Por favor, especifique el tipo de dispositivo.";
        return;
    }
    if (!this.form.nombre || this.form.campos.length === 0 || this.form.campos.some(c => !c.nombre || !c.unidad_medida_id)) {
        this.error = "Complete el nombre del sensor y asegure que cada campo tenga Nombre y Unidad.";
        return;
    }
    
    // 🚨 PASO DE DEPURACIÓN CRÍTICO: Serializar e Imprimir el Payload
    const payload = JSON.stringify(this.form, null, 2);
    
    // 🚨 NUEVA FUNCIÓN: Mostrar el JSON al usuario para confirmación
    const confirmSend = confirm(
        "Verifique el JSON antes de enviar. Si es correcto, presione Aceptar.\n\n" + 
        "--- PAYLOAD JSON ---\n" + payload
    );

    if (!confirmSend) {
        return; // Detiene el envío si el usuario presiona Cancelar
    }
    
    this.loading = true;
    this.error = null;
    const token = localStorage.getItem('accessToken');
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/sensores/`, { 
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
            body: payload // 🚨 Envía el JSON pre-serializado
        });

        const data = await response.json();

        if (!response.ok) {
            // Manejar errores de validación de FastAPI
            let errorMessage = data.message || data.detail || 'Fallo al crear el sensor.';
            
            if (data.detail && Array.isArray(data.detail)) {
                // Si el 422 contiene detalles, los mostramos
                errorMessage = "Error de validación: Revise los tipos de datos.";
            }

            throw new Error(errorMessage);
        }
        
        this.$emit('sensor-creado', data.resultados[0]);
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