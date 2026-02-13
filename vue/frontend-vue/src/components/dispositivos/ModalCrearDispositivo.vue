<template>
  <div class="modal-base" @click.self="$emit('close')">
    <div class="modal-contenido" :class="{ 'theme-dark': isDark, 'theme-light': !isDark }">
      
      <div class="modal-header">
        <h2>Agregar Nuevo Dispositivo al Proyecto {{ proyectoId }}</h2>
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
              <h4 class="location-heading">Ubicación (Pin Drop)</h4>
              <p class="location-note">Mueve el marcador o haz clic en el mapa para establecer la ubicación exacta.</p>
              
              <div id="leaflet-map-container" style="height: 300px; margin-bottom: 15px;"></div>
              
              <div class="form-row">
                <div class="form-group">
                  <label for="latitud">Latitud:</label>
                  <input type="text" v-model="form.latitud" id="latitud" class="form-control" readonly>
                </div>
                <div class="form-group">
                  <label for="longitud">Longitud:</label>
                  <input type="text" v-model="form.longitud" id="longitud" class="form-control" readonly>
                </div>
              </div>
            </div>
          </form>
        </div>
      </div> 
      <div class="modal-footer-actions">
        <button type="button" @click="$emit('close')" class="btn btn-secondary me-2">Cancelar</button>
        <button type="submit" @click="submitDispositivo" class="btn btn-primary" :disabled="loading">
          <i v-if="loading" class="bi bi-arrow-clockwise fa-spin"></i>
          {{ loading ? 'Guardando...' : 'Guardar Dispositivo' }}
        </button>
      </div>
      
    </div>
  </div>
</template>

<script>
import L from 'leaflet';

// ⭐ Agregar esta línea obligatoria
import 'leaflet/dist/leaflet.css';

import 'leaflet-control-geocoder/dist/Control.Geocoder.css';
import 'leaflet-control-geocoder';

import marker2x from 'leaflet/dist/images/marker-icon-2x.png';
import markerIcon from 'leaflet/dist/images/marker-icon.png';
import markerShadow from 'leaflet/dist/images/marker-shadow.png';

L.Icon.Default.mergeOptions({
  iconRetinaUrl: marker2x,
  iconUrl: markerIcon,
  shadowUrl: markerShadow,
});

// ⭐ FIX → Control de localización personalizado
L.Control.CustomLocate = L.Control.extend({
    onAdd: function(map) {
        const container = L.DomUtil.create('div', 'leaflet-bar leaflet-control');
        container.innerHTML = '<i class="bi bi-geo-alt-fill" style="font-size:18px; margin:auto; display:flex; justify-content:center; align-items:center;"></i>';
        container.style.cursor = 'pointer';
        container.onclick = () => map.locate({ setView: true, maxZoom: 16, enableHighAccuracy: true });
        return container;
    },
    onRemove: function() {}
});
L.control.customLocate = function(opts) { return new L.Control.CustomLocate(opts); }

export default {
    name: 'ModalCrearDispositivo',
    props: ['proyectoId'],
    data() {
        return {
            isDark: false,
            loading: false,
            error: null,
            tiposDispositivo: ['Microcontrolador', 'Raspberry Pi', 'Sensor Gateway', 'Controlador'],
            map: null,
            marker: null,
            tipoSeleccionado: 'Microcontrolador',
            form: {
                nombre: '',
                descripcion: '',
                tipo: 'Microcontrolador',
                latitud: null,
                longitud: null,
                habilitado: true,
                proyecto_id: this.proyectoId
            }
        };
    },
    watch: {
        tipoSeleccionado(v) {
            this.form.tipo = (v !== 'Otro') ? v : '';
        },
    },
    mounted() {
        this.isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

        this.$nextTick(() => this.initMap());
    },
    methods: {
        initMap() {
            const lat = 20.501, lng = -87.001;

            this.map = L.map('leaflet-map-container').setView([lat, lng], 13);

            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(this.map);

            this.marker = L.marker([lat, lng], { draggable: true }).addTo(this.map);
            this.updateCoordinates(lat, lng);

            // ⭐ FIX → Geocoder con estilos cargados
            L.Control.geocoder({ defaultMarkGeocode: false })
            .on('markgeocode', e => {
                const pos = e.geocode.center;
                this.marker.setLatLng(pos);
                this.map.fitBounds(e.geocode.bbox);
                this.updateCoordinates(pos.lat, pos.lng);
            }).addTo(this.map);

            // ⭐ FIX → Botón de localizar estable
            L.control.customLocate({ position: 'topleft' }).addTo(this.map);

            // ⭐ FIX → Handler de error de geolocalización
            this.map.on('locationerror', () => {
                alert("No se pudo obtener la ubicación. Revisar permisos de GPS.");
            });

            this.map.on('locationfound', e => {
                this.marker.setLatLng(e.latlng);
                this.updateCoordinates(e.latlng.lat, e.latlng.lng);
            });

            this.marker.on('dragend', e => {
                const p = e.target.getLatLng();
                this.updateCoordinates(p.lat, p.lng);
            });

            this.map.on('click', e => {
                this.marker.setLatLng(e.latlng);
                this.updateCoordinates(e.latlng.lat, e.latlng.lng);
            });

            setTimeout(() => this.map.invalidateSize(), 200);
        },
        updateCoordinates(lat, lng) {
            this.form.latitud = Number(lat).toFixed(6);
            this.form.longitud = Number(lng).toFixed(6);
        },
        async submitDispositivo() {
            if (!this.form.nombre || !this.form.tipo)
                return this.error = "Faltan campos obligatorios.";

            this.loading = true;
            this.error = null;

            try {
                const token = localStorage.getItem('accessToken');

                const res = await fetch(`${API_BASE_URL}/api/dispositivos/`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(this.form)
                });

                const data = await res.json();

                if (!res.ok) throw new Error(data.message || 'Error al crear el dispositivo.');

                this.$emit('dispositivo-creado', data.resultados[0]);
                this.$emit('close');

            } catch (err) {
                this.error = err.message;
            } finally {
                this.loading = false;
            }
        },
    }
};
</script>




<style scoped lang="scss">
@use 'sass:color'; // 🚨 CRÍTICO: Importar el módulo de color para usar color.adjust()
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