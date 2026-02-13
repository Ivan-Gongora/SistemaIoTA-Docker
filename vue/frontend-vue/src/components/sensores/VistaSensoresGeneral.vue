<template>
  <div class="plataforma-layout" :class="{ 'theme-dark': isDark, 'theme-light': !isDark }">
    
    <BarraLateralPlataforma :is-open="isSidebarOpen" />
    
    <div class="plataforma-contenido" :class="{ 'shifted': isSidebarOpen }">
      
      <EncabezadoPlataforma 
        titulo="Sensores (Global)"
        subtitulo="Vista de todos los sensores agrupados por proyecto"
        @toggle-sidebar="toggleSidebar" 
        :is-sidebar-open="isSidebarOpen"
      />

      <div class="sensores-general-contenido">
        
        <div class="controls-header">
            <div class="total-info">
                <span class="count-badge">{{ totalRecords }}</span> Sensores detectados
            </div>
            
            <div class="search-box">
                <i class="bi bi-search search-icon"></i>
                <input 
                    type="text" 
                    v-model="searchQuery" 
                    @input="onSearchInput" 
                    placeholder="Buscar..." 
                    class="search-input"
                >
            </div>
        </div>

        <div v-if="loading" class="alert-info">
            <i class="bi bi-arrow-clockwise fa-spin"></i> Cargando sensores...
        </div>
        <div v-else-if="error" class="alert-error">{{ error }}</div>
        
        <div v-else-if="sensores.length === 0" class="alert-empty">
          <i class="bi bi-box-fill"></i> No se encontraron sensores.
        </div>
        
        <div v-else class="ecosystem-list">
          
          <div 
            v-for="(proyectoData, nombreProyecto) in sensoresAgrupados" 
            :key="nombreProyecto" 
            class="proyecto-bloque"
          >
            <h2 class="proyecto-titulo">
                <span class="marker"></span> {{ nombreProyecto }}
            </h2>

            <div 
              v-for="(dispositivoData, nombreDispositivo) in proyectoData.dispositivos" 
              :key="nombreDispositivo" 
              class="dispositivo-group"
            >
              <h3 class="dispositivo-titulo">{{ nombreDispositivo }}</h3>
              
              <div class="sensors-stack">
                    <div 
                        v-for="sensor in dispositivoData.sensores" 
                        :key="sensor.id" 
                        class="sensor-strip" 
                        @click="navigateToSensorDetail(sensor.id)"
                    >
                        <div class="strip-icon">
                             <i class="bi bi-activity"></i>
                        </div>

                        <div class="strip-info">
                            <span class="sensor-name">{{ sensor.nombre }}</span>
                            <span class="sensor-type">{{ sensor.tipo }}</span>
                        </div>

                        <div class="strip-meta">
                            <span class="meta-label">Campos</span>
                            <span class="meta-value">{{ sensor.total_campos || 0 }}</span>
                        </div>

                        <div class="strip-status">
                            <span class="status-pill" :class="sensor.habilitado ? 'status-on' : 'status-off'">
                                <i :class="sensor.habilitado ? 'bi bi-check-circle-fill' : 'bi bi-x-circle-fill'"></i>
                                {{ sensor.habilitado ? 'Activo' : 'Inactivo' }}
                            </span>
                        </div>

                        <div class="strip-actions">
                            
                            <button 
                                @click.stop="navigateToSensorDetail(sensor.id)" 
                                class="action-btn view" 
                                title="Ver Detalles"
                            >
                                <i class="bi bi-eye-fill"></i>
                            </button>

                            <template v-if="sensor.mi_rol === 'Propietario' || sensor.mi_rol === 'Colaborador'">
                                <button 
                                    @click.stop="openEditSensorModal(sensor)" 
                                    class="action-btn edit" 
                                    title="Editar"
                                >
                                    <i class="bi bi-pencil-fill"></i>
                                </button>
                                
                                <button 
                                    @click.stop="confirmarEliminacionSensor(sensor.id, sensor.nombre)" 
                                    class="action-btn delete" 
                                    title="Eliminar"
                                >
                                    <i class="bi bi-trash-fill"></i>
                                </button>
                            </template>

                        </div>
                        
                    </div>
              </div>
            </div>
          </div>
        </div>

        <div class="pagination-controls" v-if="totalPages > 1 && !loading">
            <button class="btn-page" :disabled="page === 1" @click="changePage(page - 1)">
                <i class="bi bi-chevron-left"></i>
            </button>
            <span class="page-info">Página {{ page }} de {{ totalPages }}</span>
            <button class="btn-page" :disabled="page === totalPages" @click="changePage(page + 1)">
                <i class="bi bi-chevron-right"></i>
            </button>
        </div>

      </div>
    </div>
    
    <ModalEditarSensor v-if="mostrarModalEditarSensor" :sensor-id="sensorSeleccionado" @sensor-actualizado="handleSensorUpdated" @close="closeEditSensorModal" />
    <ModalEliminarSensor v-if="mostrarModalEliminarSensor" :sensor-id="sensorEliminarId" :sensor-nombre="sensorEliminarNombre" @cancelar="cancelarEliminacionSensor" @confirmar="ejecutarEliminacionSensor(sensorEliminarId)" />
  </div>
</template>

<script>
// Componentes de Layout
import BarraLateralPlataforma from '../plataforma/BarraLateralPlataforma.vue';
import EncabezadoPlataforma from '../plataforma/EncabezadoPlataforma.vue';
// Importamos los modales si los vamos a usar aquí
import ModalEditarSensor from './ModalEditarSensor.vue'; 
import ModalEliminarSensor from './ModalEliminarSensor.vue';
import debounce from 'lodash/debounce';
// const API_BASE_URL = 'http://127.0.0.1:8001';

export default {
    name: 'VistaSensoresGeneral',
    components: {
        BarraLateralPlataforma,
        EncabezadoPlataforma,
        ModalEditarSensor,
        ModalEliminarSensor,
    },
    data() {
        return {
            isDark: false,
            isSidebarOpen: true,
            loading: true,
            error: null,
            sensores: [], // La lista plana de la API
            
            // Estados de Modales
            mostrarModalEditarSensor: false,
            sensorSeleccionado: null,

            mostrarModalEliminarSensor: false,
            sensorEliminarId: null,
            sensorEliminarNombre: null,

            searchQuery: '',
            page: 1,
            limit: 10, 
            totalRecords: 0,
        };

    },
    computed: {
        //  Agrupación Doble (Proyecto -> Dispositivo -> Sensores)
        sensoresAgrupados() {
            const grupos = {};
            for (const sensor of this.sensores) {
                const proyecto = sensor.nombre_proyecto || 'Sin Proyecto';
                const dispositivo = sensor.nombre_dispositivo || 'Sin Dispositivo';

                if (!grupos[proyecto]) {
                    grupos[proyecto] = { nombre: proyecto, dispositivos: {} };
                }
                
                if (!grupos[proyecto].dispositivos[dispositivo]) {
                    grupos[proyecto].dispositivos[dispositivo] = { nombre: dispositivo, sensores: [] };
                }
                
                grupos[proyecto].dispositivos[dispositivo].sensores.push(sensor);
            }
            return grupos;
        }
    },created() {
        this.debouncedSearch = debounce(() => {
            this.page = 1;
            this.cargarSensoresGlobales();
        }, 500);
    },
    mounted() {
        this.cargarSensoresGlobales();
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
        onSearchInput() {
            this.debouncedSearch();
        },

        changePage(newPage) {
            if (newPage >= 1 && newPage <= this.totalPages) {
                this.page = newPage;
                this.cargarSensoresGlobales();
                // Scroll suave al inicio
                window.scrollTo({ top: 0, behavior: 'smooth' });
            }
        },
        
        async cargarSensoresGlobales() {
            this.loading = true;
            this.error = null;
            const token = localStorage.getItem('accessToken');
            if (!token) { this.$router.push('/'); return; }

            const params = new URLSearchParams({
                page: this.page,
                limit: this.limit,
                search: this.searchQuery
            });

            try {
                const response = await fetch(`${API_BASE_URL}/api/sensores/todos?${params}`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                
                if (!response.ok) {
                     const err = await response.json();
                     throw new Error(err.detail || 'Fallo al obtener sensores.');
                }
                
                const respuesta = await response.json();
                // { data, total, total_pages }
                this.sensores = respuesta.data;
                this.totalRecords = respuesta.total;
                this.totalPages = respuesta.total_pages;

            } catch (err) {
                this.error = err.message;
                this.sensores = [];
            } finally {
                this.loading = false;
            }
        },
        
        // --- Navegación ---
        navigateToSensorDetail(sensorId) {
            // Navega a la vista de campos de este sensor
            this.$router.push(`/detalle-sensor/${sensorId}`);
        },

        // --- Lógica de Modales ---
        openEditSensorModal(sensor) {
            this.sensorSeleccionado = sensor.id;
            this.mostrarModalEditarSensor = true;
        },
        closeEditSensorModal() {
            this.mostrarModalEditarSensor = false;
            this.sensorSeleccionado = null;
        },
        handleSensorUpdated() {
            this.closeEditSensorModal();
            this.cargarSensoresGlobales(); // Recargar todo
        },
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
                    method: 'DELETE', headers: { 'Authorization': `Bearer ${token}` },
                });
                if (!response.ok) {
                     const err = await response.json();
                     if (response.status === 403) throw new Error(err.detail || "No tienes permiso para eliminar este sensor.");
                     throw new Error(err.message || 'Fallo al eliminar.');
                }
                alert('Sensor eliminado.');
                this.cancelarEliminacionSensor();
                this.cargarSensoresGlobales(); 
            } catch (err) {
                alert('Error: ' + err.message);
                this.cancelarEliminacionSensor();
            }
        },

        // --- Lógica de Layout ---
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
@use "sass:color";
.sensores-general-contenido { 
    padding: 0 40px 40px 40px; 
}

// ------------------------------------------------
// CONTROLES Y BUSCADOR
// ------------------------------------------------
.controls-header {
    display: flex; justify-content: space-between; align-items: center; 
    margin-bottom: 40px; flex-wrap: wrap; gap: 15px;
    
    .total-info { 
        font-size: 1.1rem; font-weight: 500; color: $GRAY-COLD; 
        .count-badge { 
            background-color: $PRIMARY-PURPLE; color: $WHITE; 
            padding: 2px 10px; border-radius: 12px; 
            font-weight: 700; margin-right: 5px; 
        }
    }
    
    .search-box { 
        position: relative; 
        .search-input { 
            padding: 10px 15px 10px 40px; border-radius: 12px; 
            border: 1px solid transparent; 
            width: 250px; outline: none; font-size: 0.95rem;
            transition: all 0.3s ease;
            
            &:focus { 
                width: 300px; 
                border-color: $PRIMARY-PURPLE; 
                box-shadow: 0 0 0 3px rgba($PRIMARY-PURPLE, 0.1);
            } 
        }
        .search-icon { 
            position: absolute; left: 15px; top: 50%; 
            transform: translateY(-50%); color: $GRAY-COLD; 
        }
    }
}

// ------------------------------------------------
// ESTRUCTURA DE LISTA
// ------------------------------------------------
.proyecto-bloque {
    margin-bottom: 40px;
}

.proyecto-titulo {
    font-size: 1.2rem; font-weight: 700; margin-bottom: 20px;
    display: flex; align-items: center; gap: 10px;
    
    .marker {
        width: 4px; height: 20px; background-color: $PRIMARY-PURPLE;
        border-radius: 2px; display: inline-block;
    }
}

.dispositivo-group {
    margin-bottom: 25px;
    padding-left: 15px; 
    border-left: 1px solid rgba($GRAY-COLD, 0.2); 
}

.dispositivo-titulo {
    font-size: 0.95rem; font-weight: 600; color: $GRAY-COLD;
    margin-bottom: 15px; padding-left: 10px; text-transform: uppercase; letter-spacing: 0.5px;
}

.sensors-stack {
    display: flex; flex-direction: column; gap: 10px;
}

// ------------------------------------------------
// SENSOR STRIP (Elemento Individual)
// ------------------------------------------------
.sensor-strip {
    display: grid;
    grid-template-columns: 50px 2fr 1fr 1fr auto; 
    align-items: center;
    padding: 15px 20px;
    border-radius: 12px; 
    cursor: pointer;
    transition: all 0.2s ease-in-out;
    border: 1px solid transparent;
    
    &:hover {
        transform: translateX(5px); 
        .strip-actions { opacity: 1; pointer-events: auto; }
    }
}

.strip-icon {
    font-size: 1.5rem; color: $PRIMARY-PURPLE;
    display: flex; justify-content: center; align-items: center;
}

.strip-info {
    display: flex; flex-direction: column;
    .sensor-name { font-weight: 600; font-size: 1rem; margin-bottom: 2px; }
    .sensor-type { font-size: 0.8rem; opacity: 0.7; }
}

.strip-meta {
    display: flex; flex-direction: column; align-items: flex-start;
    .meta-label { font-size: 0.7rem; text-transform: uppercase; opacity: 0.6; }
    .meta-value { font-weight: 700; font-size: 1.1rem; }
}

.strip-status {
    .status-pill {
        display: inline-flex; align-items: center; gap: 6px;
        padding: 6px 12px; border-radius: 20px;
        font-size: 0.8rem; font-weight: 600;
        
        &.status-on { background-color: rgba($SUCCESS-COLOR, 0.1); color: $SUCCESS-COLOR; }
        &.status-off { background-color: rgba($GRAY-COLD, 0.1); color: $GRAY-COLD; }
    }
}
.strip-actions {
    display: flex; gap: 10px;
    opacity: 0.6; // Semi-transparente por defecto
    transition: opacity 0.2s;

    .action-btn {
        background: none; border: none; cursor: pointer;
        width: 35px; height: 35px; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-size: 1rem; transition: background 0.2s;
        
        // 🚨 NUEVO: Estilo para el botón Ver
        &.view { 
            color: $PRIMARY-PURPLE; 
            &:hover { background-color: rgba($PRIMARY-PURPLE, 0.1); } 
        }
        
        // Estilos existentes
        &.edit { 
            color: $INFO-COLOR; 
            &:hover { background-color: rgba($INFO-COLOR, 0.1); } 
        }
        &.delete { 
            color: $DANGER-COLOR; 
            &:hover { background-color: rgba($DANGER-COLOR, 0.1); } 
        }
    }
}
.sensor-strip:hover .strip-actions { opacity: 1; pointer-events: auto; }
// ------------------------------------------------
// PAGINACIÓN
// ------------------------------------------------
.pagination-controls { 
    display: flex; justify-content: center; align-items: center; gap: 20px; margin-top: 40px; 
    .btn-page { 
        background: none; border: 1px solid $PRIMARY-PURPLE; 
        color: $PRIMARY-PURPLE; padding: 8px 18px; border-radius: 8px; 
        font-weight: 600; cursor: pointer; transition: all 0.2s;
        
        &:hover:not(:disabled) { background-color: $PRIMARY-PURPLE; color: $WHITE; }
        &:disabled { border-color: $GRAY-COLD; color: $GRAY-COLD; cursor: not-allowed; opacity: 0.5; }
    }
    .page-info { font-weight: 500; color: $GRAY-COLD; }
}

// ------------------------------------------------
// TEMAS (CORREGIDOS)
// ------------------------------------------------

// TEMA OSCURO
.theme-dark {
      background-color: $DARK-BG-CONTRAST; 
    color: $LIGHT-TEXT;
    
    .search-input { 
        background-color: $DARK-INPUT-BG; 
        border-color: rgba($WHITE, 0.1); 
        color: $LIGHT-TEXT; 
    }
    
    .proyecto-titulo { color: $LIGHT-TEXT; }
    
    .sensor-strip {
        background-color: $SUBTLE-BG-DARK; // Usar variable global oscura
        border-bottom: 1px solid rgba($WHITE, 0.05); 
        box-shadow: 0 2px 4px rgba(0,0,0,0.2); // Sombra oscura sutil
        
        &:hover { background-color: color.adjust($SUBTLE-BG-DARK, $lightness: 5%); }
        
        .sensor-name { color: $LIGHT-TEXT; }
        .sensor-type { color: $GRAY-COLD; }
        .meta-value { color: $LIGHT-TEXT; }
        .meta-label { color: $GRAY-COLD; }
    }

    .alert-info, .alert-empty { color: $GRAY-COLD; text-align: center; margin-top: 30px; }
}

// TEMA CLARO
.theme-light {
    .search-input { 
        background-color: $LIGHT-INPUT-BG; 
        border-color: $LIGHT-BORDER; 
        color: $DARK-TEXT; 
    }
    
    .proyecto-titulo { color: $DARK-TEXT; }
    
    .sensor-strip {
        background-color: $WHITE; 
        border: 1px solid $LIGHT-BORDER; 
        box-shadow: 0 2px 5px rgba(0,0,0,0.03); 
        
        &:hover { 
            border-color: $PRIMARY-PURPLE; 
            box-shadow: 0 4px 12px rgba($PRIMARY-PURPLE, 0.15);
        }

        .sensor-name { color: $DARK-TEXT; }
        .sensor-type { color: $GRAY-COLD; }
        .meta-value { color: $DARK-TEXT; }
        .meta-label { color: $GRAY-COLD; }
    }

    .alert-info, .alert-empty { color: $GRAY-COLD; text-align: center; margin-top: 30px; }
}

// Responsive
@media (max-width: 768px) {
    .sensor-strip {
        grid-template-columns: 1fr auto; gap: 15px; padding: 15px;
        .strip-icon, .strip-meta { display: none; }
    }
}
</style>