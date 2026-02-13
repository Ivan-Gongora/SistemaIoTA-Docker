<template>
  <div class="modal-base" @click.self="$emit('close')">
    <div class="modal-contenido" :class="{ 'theme-dark': isDark, 'theme-light': !isDark }">
      
      <div class="modal-header">
        <h2>Modificar Dispositivo: {{ dispositivoActual.nombre }}</h2>
        <button @click="$emit('close')" class="btn-cerrar">&times;</button>
      </div>

      <div class="modal-scroll-body">
        <div class="modal-body">
          <div v-if="error" class="alert-error">{{ error }}</div>
          
          <form @submit.prevent="submitDispositivo">
            
            <div class="form-row">
              <div class="form-group">
                <label for="nombre">Nombre:</label>
                <input type="text" v-model="form.nombre" id="nombre" class="form-control" required>
              </div>
              <div class="form-group">
                <label for="tipo">Tipo de Dispositivo:</label>
                <select v-model="tipoSeleccionado" id="tipo" class="form-control" required>
                  <option v-for="t in tiposDispositivo" :key="t" :value="t">{{ t }}</option>
                  <option value="Otro">Otro (Especifique)</option>
                </select>
              </div>
            </div>
            
            <div v-if="tipoSeleccionado === 'Otro'" class="form-group mb-3 full-width">
              <label for="otro_tipo">Especifique el Tipo:</label>
              <input type="text" v-model="form.tipo" id="otro_tipo" class="form-control" required placeholder="Ej: Módulo de Relevo PLC">
            </div>
            
            <div class="form-group mb-3">
              <label for="descripcion">Descripción:</label>
              <textarea v-model="form.descripcion" id="descripcion" class="form-control" rows="2"></textarea>
            </div>
            
            <div class="location-group">
              <h4 class="location-heading">Ubicación (Manual)</h4>
              <p class="location-note">
                  La funcionalidad de mapa ha sido desactivada temporalmente. Ingrese coordenadas.
              </p>
              <div class="form-row">
                <div class="form-group">
                  <label for="latitud">Latitud:</label>
                  <input type="number" step="any" v-model.number="form.latitud" id="latitud" class="form-control" placeholder="20.501">
                </div>
                <div class="form-group">
                  <label for="longitud">Longitud:</label>
                  <input type="number" step="any" v-model.number="form.longitud" id="longitud" class="form-control" placeholder="-87.001">
                </div>
              </div>
            </div>

            <div class="form-group mb-4">
                <label for="habilitado">Estado del Dispositivo:</label>
                <select v-model="form.habilitado" id="habilitado" class="form-control">
                    <option :value="true">Habilitado (Activo)</option>
                    <option :value="false">Deshabilitado (Inactivo)</option>
                </select>
            </div>

          </form>
        </div>
      </div>
      
      <div class="modal-footer-actions">
        <button type="button" @click="$emit('close')" class="btn btn-secondary me-2">Cancelar</button>
        <button type="submit" @click="submitDispositivo" class="btn btn-primary" :disabled="loading">
          <i v-if="loading" class="bi bi-arrow-clockwise fa-spin"></i>
          {{ loading ? 'Guardando...' : 'Guardar Cambios' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>


export default {
    name: 'ModalEditarDispositivo',
    props: {
        dispositivoActual: { type: Object, required: true }
        
    },
    data() {
        // Inicialización de la data del formulario
        const formInitialData = {
          
            // Copia todos los campos necesarios de la prop
            nombre: this.dispositivoActual.nombre || '',
            descripcion: this.dispositivoActual.descripcion || '',
            tipo: this.dispositivoActual.tipo || 'Microcontrolador',
            latitud: this.dispositivoActual.latitud || null, 
            longitud: this.dispositivoActual.longitud || null,
            habilitado: this.dispositivoActual.habilitado === 1 || this.dispositivoActual.habilitado === true,
            proyecto_id: this.dispositivoActual.proyecto_id,
        };

        return {
            isDark: false,
            loading: false,
            error: null,
            tiposDispositivo: ['Microcontrolador', 'Raspberry Pi', 'Sensor Gateway', 'Controlador'],
            
            tipoSeleccionado: formInitialData.tipo, // Control del dropdown
            form: formInitialData,
        };
    },
    watch: {
        // VIGILANTE: Sincroniza el campo 'tipo' para el envío a la API
        tipoSeleccionado(newValue) {
            this.form.tipo = (newValue !== 'Otro') ? newValue : ''; 
        },
        // VIGILANTE: Si el dispositivo cambia (necesario para el modal)
        dispositivoActual: {
            handler(newDevice) {
                this.form = { ...newDevice, habilitado: newDevice.habilitado === 1 || newDevice.habilitado === true, };
                this.tipoSeleccionado = newDevice.tipo || 'Microcontrolador';
            },
            deep: true
        }
    },
    mounted() {
         if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            this.isDark = true;
        }
    },
    methods: {
        // ... (submitDispositivo - Lógica de envío PUT a la API)
        async submitDispositivo() {
            if (this.tipoSeleccionado === 'Otro' && !this.form.tipo) {
                this.error = "Por favor, especifique el tipo de dispositivo.";
                return;
            }
            // ... (validación de campos obligatorios) ...
            
            this.loading = true;
            this.error = null;
            const token = localStorage.getItem('accessToken');
            
            try {
                // 🚨 CRÍTICO: Usar el método PUT y enviar el ID del dispositivo en la URL
                const response = await fetch(`${API_BASE_URL}/api/dispositivos/${this.dispositivoActual.id}`, {
                    method: 'PUT',
                    headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
                    body: JSON.stringify(this.form)
                });

                const data = await response.json();

                if (!response.ok) {
                    throw new Error(data.message || data.detail || 'Fallo al actualizar el dispositivo.');
                }
                
                this.$emit('dispositivo-actualizado', data.resultados[0]);
                this.$emit('close');

            } catch (err) {
                this.error = err.message || 'Error de conexión.';
            } finally {
                this.loading = false;
            }
        },
        // ... (métodos de detección de tema)
    }
};
</script>


<style scoped lang="scss">
// // ----------------------------------------
// // VARIABLES DE LA PALETA
// // ----------------------------------------
// $PRIMARY-PURPLE: #8A2BE2;
// $SUCCESS-COLOR: #1ABC9C;
// $BLUE-MIDNIGHT: #1A1A2E;
// $DARK-TEXT: #333333;
// $LIGHT-TEXT: #E4E6EB;
// $SUBTLE-BG-DARK: #2B2B40; 
// $SUBTLE-BG-LIGHT: #FFFFFF;
// $WHITE-SOFT: #F7F9FC;
// $GRAY-COLD: #99A2AD;


// ----------------------------------------
// BASE DEL MODAL (POSICIONAMIENTO)
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

// ----------------------------------------
// CABECERA Y CUERPO SCROLLABLE
// ----------------------------------------

.modal-header {
    display: flex; justify-content: space-between; align-items: center;
    padding: 20px 25px; /* Padding Fijo */
    flex-shrink: 0; /* Evita que el header se encoja */
    border-bottom: 1px solid rgba($GRAY-COLD, 0.1);
    h2 { font-size: 1.4rem; font-weight: 600; }
}

.modal-scroll-body {
    // 🚨 HABILITA LA BARRA DE DESPLAZAMIENTO
    flex-grow: 1; 
    overflow-y: auto; 
    padding: 0 25px; /* Mantiene el padding lateral */
}

.modal-body {
    padding-top: 20px; /* Añadir espacio arriba del formulario */
    padding-bottom: 20px;
}

.form-row { display: flex; gap: 20px; }
.form-group { flex: 1; margin-bottom: 15px; }

// ----------------------------------------
// FOOTER FIJO (Botones)
// ----------------------------------------
.modal-footer-actions {
    // 🚨 MANTIENE LOS BOTONES VISIBLES
    flex-shrink: 0; 
    padding: 15px 25px; 
    border-top: 1px solid rgba(0, 0, 0, 0.1);
    background-color: inherit; 
    display: flex;
    justify-content: flex-end;
    gap: 10px;
}

// ----------------------------------------
// ESTILOS DE MAPA Y FORMULARIO
// ----------------------------------------
.location-group { margin-top: 20px; }
.location-heading { font-size: 1.2rem; margin-bottom: 5px; }
.location-note { font-size: 0.85rem; opacity: 0.7; margin-bottom: 10px; }


// ----------------------------------------
// TEMAS (DARK/LIGHT)
// ----------------------------------------
.theme-light { 
    background-color: $SUBTLE-BG-LIGHT; color: $DARK-TEXT; 
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