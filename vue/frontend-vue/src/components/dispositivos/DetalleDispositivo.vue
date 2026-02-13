<template>
  <div class="plataforma-layout" :class="{ 'theme-dark': isDark, 'theme-light': !isDark }">
    
    <BarraLateralPlataforma :is-open="isSidebarOpen" />
    
    <div class="plataforma-contenido" :class="{ 'shifted': isSidebarOpen }">
      
      <EncabezadoPlataforma 
        :titulo="dispositivo.nombre || 'Cargando...'"
        :subtitulo="'Tipo: ' + (dispositivo.tipo || 'N/A')"
        @toggle-sidebar="toggleSidebar" 
        :is-sidebar-open="isSidebarOpen"
      >
        <template #title-prefix>
             <button @click="goBack" class="btn-back"><i class="bi bi-arrow-left-circle-fill"></i></button>
        </template>
      </EncabezadoPlataforma>

      <div class="detalle-dispositivo-contenido">
        
        <div class="sensores-header">
            <h2>Sensores Conectados ({{ totalRecords }})</h2>
            
            <div class="actions-group">
                <div class="search-box">
                    <i class="bi bi-search"></i>
                    <input 
                        type="text" 
                        v-model="searchQuery" 
                        @input="onSearchInput" 
                        placeholder="Buscar dispositivo..." 
                        class="form-control-search"
                    >
                </div>
                
               <button 
                    @click="openCreateSensorModal" 
                    class="btn-primary-action" 
                    v-if="miRol === 'Propietario' ||miRol === 'PROPIETARIO' || miRol === 'Colaborador' || miRol === 'COLABORADOR'"
                    >
                        <i class="bi bi-plus-circle-fill"></i> Agregar Sensor
                    </button>
            </div>
        </div>

        <div v-if="loading" class="alert-info">
            <i class="bi bi-arrow-clockwise fa-spin"></i> Cargando sensores...
        </div>
        <div v-else-if="error" class="alert-error">{{ error }}</div>
        
        <div v-else-if="sensores.length > 0" class="sensores-grid">
            <TarjetaSensor 
                v-for="sensor in sensores" 
                :key="sensor.id"
                :sensor="sensor"
                :is-dark="isDark"
                @edit-sensor="openEditSensorModal"
                @delete-sensor="confirmarEliminacionSensor" 
            />
        </div>
        
        <div v-else class="alert-empty-data">
            Este dispositivo no tiene sensores registrados.
        </div>

        <div class="pagination-controls" v-if="totalPages > 1">
            <button class="btn-page" :disabled="page === 1" @click="changePage(page - 1)">
                <i class="bi bi-chevron-left"></i>
            </button>
            <span class="page-info">Pág {{ page }} de {{ totalPages }}</span>
            <button class="btn-page" :disabled="page === totalPages" @click="changePage(page + 1)">
                <i class="bi bi-chevron-right"></i>
            </button>
        </div>

      </div>
    </div>
    
    <ModalCrearSensor v-if="mostrarModalCrearSensor" :dispositivo-id="dispositivoId" @sensor-creado="handleSensorCreated" @close="closeCreateSensorModal" />
    <ModalEditarSensor v-if="mostrarModalEditarSensor" :sensor-id="sensorSeleccionado" @sensor-actualizado="handleSensorUpdated" @close="closeEditSensorModal" />
    <ModalEliminarSensor v-if="mostrarModalEliminarSensor" :sensor-id="sensorEliminarId" :sensor-nombre="sensorEliminarNombre" @cancelar="cancelarEliminacionSensor" @confirmar="ejecutarEliminacionSensor" />

  </div>
</template>

<script>
// Componentes de Layout
import BarraLateralPlataforma from '../plataforma/BarraLateralPlataforma.vue';
import EncabezadoPlataforma from '../plataforma/EncabezadoPlataforma.vue';

// Componentes de la vista actual

import TarjetaSensor from '../sensores/TarjetaSensor.vue'; 
import ModalCrearSensor from '../sensores/ModalCrearSensor.vue'; 
import ModalEditarSensor from '../sensores/ModalEditarSensor.vue'; 
import ModalEliminarSensor from '../sensores/ModalEliminarSensor.vue';

import debounce from 'lodash/debounce'; // npm install lodash


export default {
    name: 'DetalleDispositivo',
    components: {
        BarraLateralPlataforma,
        EncabezadoPlataforma,
       
        TarjetaSensor, 
        ModalCrearSensor,
        ModalEditarSensor, 
        ModalEliminarSensor,
    },
    data() {
        return {
            isDark: false, 
            isSidebarOpen: true, 
            loading: true, 
            error: null,
            dispositivo: { nombre: null, tipo: null, dispositivo_id: null },
            sensores: [],
            mostrarModalCrearSensor: false,
            mostrarModalEditarSensor: false, 
            sensorSeleccionado: null,
            mostrarModalEliminarSensor: false, 
            sensorEliminarId: null,
            sensorEliminarNombre: null,
            
            miRol: '',
            searchQuery: '',
            page: 1,
            limit: 8, // 8 sensores por página
            totalPages: 1,
            totalRecords: 0,
            loading: true,
            error: null,
            
        };
    },
    computed: {
        dispositivoId() { return this.$route.params.id; },
       
    },created() {
        this.debouncedSearch = debounce(() => {
            this.page = 1;
            this.cargarSensores();
        }, 500);
    },
    mounted() {
        this.cargarDatosIniciales();
        this.detectarTemaSistema();
        if (window.matchMedia) {
            window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', this.handleThemeChange);
        }
    },
    beforeUnmount() { 
        if (window.matchMedia) {
            window.matchMedia('(prefers-color-scheme: dark)').removeEventListener('change', this.handleThemeChange);
        }
    },
    methods: {
        async cargarDatosIniciales() {
            await this.cargarDispositivoInfo();
            await this.cargarSensores();
        },

        // 1. Cargar Info del Dispositivo (Encabezado)
        async cargarDispositivoInfo() {
            const token = localStorage.getItem('accessToken');
            if (!token || !this.dispositivoId) { this.$router.push('/'); return; }
            try {
                const response = await fetch(`${API_BASE_URL}/api/dispositivos/${this.dispositivoId}`, { headers: { 'Authorization': `Bearer ${token}` } });
                if (response.ok) {
                    this.dispositivo = await response.json();
                }
            } catch (e) { console.error(e); }
        },
        // -----------------------------------------------------
        // CONSUMO DE API: Cargar Detalles y Sensores
        // -----------------------------------------------------
        async cargarDispositivoInfo() {
            const token = localStorage.getItem('accessToken');
            if (!token || !this.dispositivoId) { this.$router.push('/'); return; }
            try {
                const response = await fetch(`${API_BASE_URL}/api/dispositivos/${this.dispositivoId}`, { headers: { 'Authorization': `Bearer ${token}` } });
                if (response.ok) {
                    this.dispositivo = await response.json();
                }
            } catch (e) { console.error(e); }
        },

        // 2. Cargar Sensores (Paginados)
     async cargarSensores() {
            this.loading = true;
            this.error = null;
            const token = localStorage.getItem('accessToken');

            const params = new URLSearchParams({
                page: this.page,
                limit: this.limit,
                search: this.searchQuery
            });

            try {
                const response = await fetch(`${API_BASE_URL}/api/sensores/dispositivo/${this.dispositivoId}?${params}`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });

                if (!response.ok) {
                    // Si es 404 en búsqueda, es lista vacía, no error fatal
                    if (response.status === 404) {
                        this.sensores = [];
                        this.totalRecords = 0;
                        this.totalPages = 1;
                        this.miRol = '';
                        return;
                    }
                    throw new Error('Fallo al obtener sensores.');
                }

                const respuesta = await response.json();

                // 👇 Nuevo: Guardar mi_rol (viene en cada sensor, pero basta con el primero)
                this.miRol = respuesta.data[0]?.mi_rol || '';

                // La API devuelve { data, total, total_pages }
                this.sensores = respuesta.data.map(s => ({
                    ...s,
                    habilitado: s.habilitado === 1 || s.habilitado === true,
                    total_campos: s.total_campos || 0
                }));

                this.totalRecords = respuesta.total;
                this.totalPages = respuesta.total_pages;

            } catch (err) {
                this.error = err.message;
                this.sensores = [];
            } finally {
                this.loading = false;
            }
        },


        onSearchInput() { this.debouncedSearch(); },
        
        changePage(newPage) {
            if (newPage >= 1 && newPage <= this.totalPages) {
                this.page = newPage;
                this.cargarSensores();
            }
        },
        
        // -----------------------------------------------------
        // GESTIÓN DE MODALES Y ACCIONES
        // -----------------------------------------------------
        
        // Creación
        openCreateSensorModal() { this.mostrarModalCrearSensor = true; },
        closeCreateSensorModal() { this.mostrarModalCrearSensor = false; },
        handleSensorCreated() {
            this.closeCreateSensorModal();
            this.cargarDatosIniciales(); // Recargar para mostrar el nuevo sensor
        },
   

            // ...
            openEditSensorModal(sensor) {
                // 1. Almacena el ID
                this.sensorSeleccionado = sensor.id; 
                // 2. Abre el modal
                this.mostrarModalEditarSensor = true;
            },

            closeEditSensorModal() {
                // Solo cierra la bandera de visualización, la limpieza se hace en el updated
                this.mostrarModalEditarSensor = false; 
                // Mantenemos el sensorSeleccionado por ahora, se limpia en handleUpdated
            },
            // DetalleDispositivo.vue (métodos)
            // DetalleDispositivo.vue
            // DetalleDispositivo.vue (métodos)
            handleSensorUpdated(data) {
                // 1. Limpieza y cierre
                this.mostrarModalEditarSensor = false;
                this.sensorSeleccionado = null;
                
                let updatedSensorData = Array.isArray(data) ? data[0] : data;

                // 🚨 CORRECCIÓN CRÍTICA: Añadir el campo 'total_campos' si falta (para que el TarjetaSensor no falle)
                if (!updatedSensorData.total_campos) {
                    // Busca el objeto original en el array para obtener el conteo de campos existente
                    const originalSensor = this.sensores.find(s => s.id === updatedSensorData.id);
                    updatedSensorData.total_campos = originalSensor ? originalSensor.total_campos : 0;
                }
                
                // 2. Actualización local
                const index = this.sensores.findIndex(s => s.id === updatedSensorData.id);

                if (index !== -1) {
                    // Actualiza el sensor directamente en el array local (splice)
                    this.sensores.splice(index, 1, updatedSensorData);
                } else {
                    // Fallback: Recarga total si el sensor no se encuentra
                    this.cargarDatosIniciales();
                }
            },
// ...
        // Eliminación
        confirmarEliminacionSensor(sensorId, nombre) {
            this.sensorEliminarId = sensorId;
            this.sensorEliminarNombre = nombre;
            this.mostrarModalEliminarSensor = true;
        },
        cancelarEliminacionSensor() {
            this.mostrarModalEliminarSensor = false;
            this.sensorEliminarId = null;
            this.sensorEliminarNombre = null;
        },
        async ejecutarEliminacionSensor(sensorId) {
            const token = localStorage.getItem('accessToken');
            try {
                const response = await fetch(`${API_BASE_URL}/api/sensores/${sensorId}`, {
                    method: 'DELETE',
                    headers: { 'Authorization': `Bearer ${token}` },
                });

                if (!response.ok) { throw new Error('Fallo al eliminar el sensor.'); }

                alert('Sensor eliminado exitosamente.');
                this.cancelarEliminacionSensor();
                this.cargarDatosIniciales(); // Recargar la lista
            } catch (err) {
                alert('Error: ' + err.message);
                this.cancelarEliminacionSensor();
            }
        },
        
        // -----------------------------------------------------
        // LÓGICA DE LAYOUT Y NAVEGACIÓN
        // -----------------------------------------------------
        goBack() { 
            // Vuelve a la vista de detalle de proyecto. Asume que el proyecto ID está en el dispositivo.
            this.$router.push(`/detalle-proyecto/${this.dispositivo.proyecto_id}`); 
        },
        toggleSidebar() { this.isSidebarOpen = !this.isSidebarOpen; },
        handleThemeChange(event) { this.isDark = event.matches; },
        detectarTemaSistema() {
            if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
                this.isDark = true;
            } else {
                this.isDark = false;
            }
        }
    }
};
</script>
<style scoped lang="scss">

.detalle-dispositivo-contenido {
    padding: 20px 40px 40px 40px; /* Padding debajo del encabezado */
}

// Estilo del botón Volver (Usado en el slot #title-prefix)
.btn-back {
    background: none;
    border: none;
    color: $DARK-TEXT;
    font-size: 1.4rem;
    margin-right: 15px;
    cursor: pointer;
    transition: color 0.2s;
    
    &:hover {
        color: $PRIMARY-PURPLE;
    }
}


// ------------------------------------
// HEADER DE SENSORES Y ACCIONES
// ------------------------------------
.sensores-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 25px;
    
    h3 {
        font-size: 1.5rem;
        font-weight: 600;
        // Color adaptado en el tema
    }
    
    .btn-primary-action {
        background-color: $SUCCESS-COLOR;
        color: white;
        border: none;
        padding: 10px 15px;
        border-radius: 8px;
        font-weight: 600;
        i { margin-right: 5px; }
    }
}

// ------------------------------------
// GRID DE SENSORES
// ------------------------------------
.sensores-grid {
    display: grid;
    /* Dos columnas para tarjetas de sensores */
    grid-template-columns: repeat(auto-fill, minmax(350px, 1fr)); 
    gap: 20px;
}

// Estilo para el mensaje de datos vacíos
.alert-empty-data {
    padding: 20px;
    border-radius: 8px;
    margin-top: 20px;
    text-align: center;
    font-style: italic;
    background-color: rgba($PRIMARY-PURPLE, 0.1);
    color: $PRIMARY-PURPLE;
}

.sensores-header {
    display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; flex-wrap: wrap; gap: 15px;
    h2 { font-size: 1.3rem; margin: 0; }
    
    .actions-group {
        display: flex; align-items: center; gap: 10px;
        
        .search-box {
        position: relative;
        input {
            padding: 8px 10px 8px 35px; border-radius: 20px; border: 1px solid #ddd;
            font-size: 0.9rem; width: 200px; transition: width 0.3s;
            &:focus { width: 250px; border-color: #8A2BE2; }
        }
        i { position: absolute; left: 12px; top: 50%; transform: translateY(-50%); color: #999; }
    }

        .btn-primary-action {
            background-color: $SUCCESS-COLOR; color: white; border: none; padding: 8px 16px; border-radius: 8px; font-weight: 600; box-shadow: 0 3px 6px rgba($SUCCESS-COLOR, 0.3);cursor: pointer;
            &:hover { opacity: 0.9; }
        }
    }
}
.pagination-controls {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 20px;
    margin-top: 50px;
    padding-bottom: 30px;
      


    .btn-page {
        background: transparent;
        border: 1px solid $PRIMARY-PURPLE;
        color: $PRIMARY-PURPLE;
        padding: 8px 18px;
        border-radius: 8px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s;
        display: flex; align-items: center; gap: 8px;
        
        &:hover:not(:disabled) {
            background-color: $PRIMARY-PURPLE;
            color: $WHITE;
        }
        &:disabled {
            border-color: $GRAY-COLD;
            color: $GRAY-COLD;
            cursor: not-allowed;
            opacity: 0.5;
        }
    }
    
    .page-info {
        font-weight: 500;
        color: $GRAY-COLD;
    }
}
// ------------------------------------
// ESTILOS DE TEMA (MODO CLARO/OSCURO)
// ------------------------------------

// MODO CLARO (Default)
.theme-light {
    background-color: $WHITE-SOFT;
    color: $DARK-TEXT;
    
    .btn-back { color: $DARK-TEXT; }
    .sensores-header h3 { color: $DARK-TEXT; }
    .form-control-search {
        background-color: $SUBTLE-BG-LIGHT;
        border-color: #ddd;
        color: $DARK-TEXT;
    }
    .form-control-search {
        background-color: $SUBTLE-BG-LIGHT; // Correcto para modo claro
        border-color: rgba($LIGHT-TEXT, 0.2);
        color: $LIGHT-TEXT;
    }
}

// MODO OSCURO
.theme-dark {
    background-color: $DARK-BG-CONTRAST; 
    color: $LIGHT-TEXT;
    
    .btn-back { color: $LIGHT-TEXT; }
    .plataforma-contenido { background-color: $DARK-BG-CONTRAST; }
    .sensores-header h3 { color: $LIGHT-TEXT; }
.form-control-search {
        background-color: $BLUE-MIDNIGHT; 
        border-color: rgba($LIGHT-TEXT, 0.2);
        color: $LIGHT-TEXT;
    }
    .alert-info {
        background-color: rgba($LIGHT-TEXT, 0.1);
        color: $LIGHT-TEXT;
    }
    .alert-error {
        background-color: rgba($DANGER-COLOR, 0.2);
        color: $LIGHT-TEXT;
    }
}
</style>