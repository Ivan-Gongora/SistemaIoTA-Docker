<template>
  <div class="plataforma-layout" :class="{ 'theme-dark': isDark, 'theme-light': !isDark }">
    <BarraLateralPlataforma :is-open="isSidebarOpen" />
    <div class="plataforma-contenido" :class="{ 'shifted': isSidebarOpen }">
      
      <EncabezadoPlataforma 
        :titulo="proyecto.nombre || 'Cargando...'"
        :subtitulo="proyecto.descripcion || 'Monitoreo IoT'"
        @toggle-sidebar="toggleSidebar" :is-sidebar-open="isSidebarOpen"
      >
        <template #title-prefix>
            <button @click="goBack" class="btn-back"><i class="bi bi-arrow-left-circle-fill"></i></button>
        </template>
      </EncabezadoPlataforma>

      <div class="proyecto-detalle-contenido">
        
        <div class="summary-cards-container">
            <TarjetaResumen 
                v-for="card in summaryCards" 
                :key="card.title" 
                :card="card"
                :is-dark="isDark"
            />
        </div>
                    
        <div class="dispositivos-header">
            <h2>Dispositivos del Proyecto ({{ totalRecords }})</h2>
            
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
                    v-if="esPropietarioOColaborador"
                    @click="openAddDeviceModal" 
                    class="btn-add-device"
                > 
                    <i class="bi bi-plus-circle-fill"></i> Nuevo Dispositivo
                </button>
            </div>
        </div>

        <div v-if="loading" class="alert-info">Cargando dispositivos...</div>
        <div v-else-if="dispositivos.length === 0" class="alert-empty-data">No se encontraron dispositivos.</div>
        
        <div v-else class="dispositivos-grid">
            <!-- Pasamos miRol al hijo para que controle sus propios botones (editar/eliminar) -->
            <TarjetaDispositivo 
                v-for="dispositivo in dispositivos"
                :key="dispositivo.id" 
                :dispositivo="dispositivo"
                :is-dark="isDark"
                :mi-rol="miRol" 
                @edit-device="openEditDeviceModal"
                @open-delete-modal="openDeleteDeviceModal"
            />
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
    
    <!-- MODALES -->
    <ModalCrearDispositivo 
        v-if="mostrarModalCrearDispositivo"
        :proyecto-id="proyectoId"
        @dispositivo-creado="handleDeviceCreated"
        @close="closeAddDeviceModal"
    />

    <ModalEditarDispositivo 
        v-if="mostrarModalEditarDispositivo"
        :dispositivo-actual="dispositivoSeleccionado"
        @dispositivo-actualizado="handleDeviceUpdated"
        @close="closeEditDeviceModal"
    />
    <ModalEliminarDispositivo 
        v-if="mostrarModalEliminarDispositivo"
        :dispositivo-id="dispositivoEliminarId"
        :dispositivo-nombre="dispositivoEliminarNombre"
        :proyecto-id="proyectoId"
        @cancelar="closeDeleteDeviceModal"
        @confirmar="eliminarDispositivo(dispositivoEliminarId, proyectoId)"
    />
  </div>
</template>

<script>
// Importa tus componentes de Layout
import BarraLateralPlataforma from '../plataforma/BarraLateralPlataforma.vue';
import EncabezadoPlataforma from '../plataforma/EncabezadoPlataforma.vue';

// Componentes de la vista actual
import TarjetaResumen from './TarjetaResumen.vue';
import TarjetaDispositivo from './TarjetaDispositivo.vue';
import ModalCrearDispositivo from '../dispositivos/ModalCrearDispositivo.vue'; 
import ModalEditarDispositivo from '../dispositivos/ModalEditarDispositivo.vue'; 
import ModalEliminarDispositivo from '../dispositivos/ModalEliminarDispositivo.vue'; 
import debounce from 'lodash/debounce'; 

// Configuración API
// const API_BASE_URL = 'http://127.0.0.1:8001'; // Ajusta según tu entorno

export default {
    name: 'DetalleProyecto',
    components: {
        BarraLateralPlataforma,
        EncabezadoPlataforma,
        TarjetaResumen,
        TarjetaDispositivo,
        ModalCrearDispositivo,
        ModalEditarDispositivo, 
        ModalEliminarDispositivo,
    },
    data() {
        return {
            isDark: false,
            isSidebarOpen: true,
            loading: true,
            error: null,
            proyecto: {},
            miRol: '', // Se llenará dinámicamente desde el backend
            dispositivos: [],
            
            // Estados de Modales
            mostrarModalCrearDispositivo: false,
            mostrarModalEditarDispositivo: false, 
            dispositivoSeleccionado: null,

            mostrarModalEliminarDispositivo: false,
            dispositivoEliminarId: null,
            dispositivoEliminarNombre: null,

            searchQuery: '',
            page: 1,
            limit: 6,
            totalPages: 1,
            totalRecords: 0,
            resumenMetricas: {},
        };
    },
    computed: {
        proyectoId() { return this.$route.params.id; },
        // Computed para simplificar la lógica del template
        esPropietarioOColaborador() {
            // Normalizamos a mayúsculas por si acaso el backend envía variantes
            const rol = (this.miRol || '').toUpperCase();
            return rol === 'PROPIETARIO'|| rol === 'Propietario '|| rol === 'Colaborador' || rol === 'COLABORADOR' || rol === 'EDITOR'; // Ajusta según tus roles reales
        },
        summaryCards() {
            const dispositivos = this.dispositivos || [];
            const activos = dispositivos.filter(d => d.habilitado).length;
            const total = this.totalRecords || 0;
            
            return [
                { title: 'Total Dispositivos', value: total, icon: 'bi bi-tablet-fill', color: '#1ABC9C' },
                { title: 'Dispositivos Activos', value: activos, icon: 'bi bi-wifi', color: '#8A2BE2' },
                { title: 'Rol Actual', value: this.miRol || 'Cargando...', icon: 'bi bi-person-badge', color: '#FFC107' },
                { title: 'Última Actividad', value: 'Hace un momento', icon: 'bi bi-activity', color: '#FF5733', isPlaceholder: true },
            ];
        }
    },
    created() {
        this.debouncedSearch = debounce(() => {
            this.page = 1;
            this.cargarDispositivos();
        }, 500);
    },
    mounted() {
        this.detectarTemaSistema();
        this.cargarDatosIniciales(); 
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
        // -----------------------------------------------------
        // LÓGICA DE CARGA DE DATOS (API)
        // -----------------------------------------------------
         async cargarDatosIniciales() {
            await this.cargarProyecto();
            await this.cargarDispositivos();
        },

        async cargarProyecto() {
            const token = localStorage.getItem('accessToken');
            if (!token) return;
            try {
                const response = await fetch(`${API_BASE_URL}/api/proyectos/${this.proyectoId}`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (response.ok) {
                    const data = await response.json();
                    this.proyecto = data;
                    // Intentamos obtener el rol del endpoint de proyecto si existe,
                    // si no, el endpoint de dispositivos lo sobreescribirá.
                    if (data.mi_rol) this.miRol = data.mi_rol;
                }
            } catch (e) { console.error("Error cargando proyecto:", e); }
        },

        //MÉTODO  PARA LEER EL NUEVO FORMATO JSON
        async cargarDispositivos() {
            this.loading = true;
            const token = localStorage.getItem('accessToken');
            
            const params = new URLSearchParams({
                page: this.page,
                limit: this.limit,
                search: this.searchQuery
            });
            
            try {
                // Endpoint actualizado: /api/dispositivos/proyecto/{id}
                const response = await fetch(`${API_BASE_URL}/api/dispositivos/proyecto/${this.proyectoId}?${params}`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                
                if (response.ok) {
                    const data = await response.json(); // Estructura: { data: [], total: #, roles_context: {} }
                    
                    // 1. EXTRAER EL ROL DEL CONTEXTO (Side-Loading)
                    if (data.roles_context && data.roles_context[this.proyectoId]) {
                        this.miRol = data.roles_context[this.proyectoId];
                        console.log("Rol obtenido del contexto de dispositivos:", this.miRol);
                    }

                    // 2. MAPEAR DISPOSITIVOS
                    // Usamos data.data porque el array viene dentro de la propiedad 'data'
                    this.dispositivos = (data.data || []).map(d => ({
                        ...d,
                        habilitado: d.habilitado === 1 || d.habilitado === true,
                        // Inyectamos el rol en el objeto por si el hijo lo necesita localmente
                        mi_rol: this.miRol,
                        // Datos simulados para vista
                        ultima_lectura: 'Sincronizando...',
                        porcentaje_carga: Math.floor(Math.random() * 100),
                    }));

                    // 3. ACTUALIZAR PAGINACIÓN
                    this.totalRecords = data.total;
                    this.totalPages = data.total_pages;

                } else {
                    this.dispositivos = [];
                    this.totalRecords = 0;
                }
            } catch (e) {
                console.error("Error cargando dispositivos:", e);
                this.error = "Error de conexión al cargar dispositivos.";
            } finally {
                this.loading = false;
            }
        },
        
        onSearchInput() { this.debouncedSearch(); },
        
        changePage(newPage) {
            if (newPage >= 1 && newPage <= this.totalPages) {
                this.page = newPage;
                this.cargarDispositivos();
            }
        },
        
        // -----------------------------------------------------
        // MANEJO DE EVENTOS DE DISPOSITIVOS
        // -----------------------------------------------------
        
        // Creación
        openAddDeviceModal() { this.mostrarModalCrearDispositivo = true; },
        closeAddDeviceModal() { this.mostrarModalCrearDispositivo = false; },
        handleDeviceCreated() {
            this.closeAddDeviceModal();
            this.cargarDispositivos(); // Recargamos la lista
        },
        
        // Edición
        openEditDeviceModal(dispositivo) {
            this.dispositivoSeleccionado = dispositivo;
            this.mostrarModalEditarDispositivo = true;
        },
        closeEditDeviceModal() {
            this.mostrarModalEditarDispositivo = false;
            this.dispositivoSeleccionado = null;
        },
        handleDeviceUpdated() {
            this.closeEditDeviceModal();
            this.cargarDispositivos();
        },

        // Eliminar (Pop-up confirmación)
        openDeleteDeviceModal(dispositivoId, nombre) {
            this.dispositivoEliminarId = dispositivoId;
            this.dispositivoEliminarNombre = nombre;
            this.mostrarModalEliminarDispositivo = true;
        },
        
        closeDeleteDeviceModal() {
            this.mostrarModalEliminarDispositivo = false;
            this.dispositivoEliminarId = null;
            this.dispositivoEliminarNombre = null;
        },
        
        async eliminarDispositivo(dispositivoId, proyectoId) {
            this.loading = true; 
            const token = localStorage.getItem('accessToken');
            const usuarioId = this.proyecto.usuario_id; 

            // Construcción URL (Si tu backend usa Query Params para DELETE)
            // Si migraste a REST estándar sería: `${API_BASE_URL}/api/dispositivos/${dispositivoId}`
            const url = `${API_BASE_URL}/api/dispositivos/?id=${dispositivoId}&proyecto_id=${proyectoId}&usuario_id=${usuarioId}`; 

            if (!token) {
                alert("Sesión no válida.");
                this.closeDeleteDeviceModal();
                this.loading = false;
                return;
            }

            try {
                const response = await fetch(url, {
                    method: 'DELETE',
                    headers: { 'Authorization': `Bearer ${token}` },
                });

                const data = await response.json();

                if (!response.ok) {
                    throw new Error(data.detail || data.message || 'Fallo al eliminar.');
                }

                alert('Dispositivo eliminado exitosamente.');
                this.closeDeleteDeviceModal();
                this.cargarDispositivos(); 

            } catch (err) {
                alert('Error: ' + err.message);
                this.closeDeleteDeviceModal();
            } finally {
                this.loading = false;
            }
        },

        // -----------------------------------------------------
        // LÓGICA DE LAYOUT Y NAVEGACIÓN
        // -----------------------------------------------------
        goBack() { this.$router.push('/mis-proyectos'); },
        toggleSidebar() { this.isSidebarOpen = !this.isSidebarOpen; },
        handleThemeChange(event) { this.isDark = event.matches; },
        detectarTemaSistema() {
            if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
                this.isDark = true;
            } else {
                this.isDark = false;
            }
        },
        formatRelativeTime(isoString) {
            if (!isoString) return 'N/A';
            return 'Hace un momento'; 
        }
    }
};
</script>

<style scoped lang="scss">

.btn-add-device {
    background-color: #1abc9c;
    color: white;
    border: none;
    padding: 0.5rem 1rem;
    border-radius: 5px;
    cursor: pointer;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    transition: background 0.3s;
}
.btn-add-device:hover {
    background-color: #16a085;
}
/* Estilos adicionales para paginación y layout */
.pagination-controls {
    display: flex;
    justify-content: center;
    align-items: center;
    margin-top: 1rem;
    gap: 1rem;
}
.btn-page {
    background: none;
    border: 1px solid #ccc;
    border-radius: 4px;
    padding: 0.25rem 0.5rem;
    cursor: pointer;
}
.btn-page:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}
.proyecto-detalle-contenido {
    padding: 20px 40px 40px 40px; 
}

// Estilo del botón Volver
.btn-back {
    background: none;
    border: none;
    color: $DARK-TEXT; /* Color en modo claro */
    font-size: 1.4rem;
    margin-right: 15px;
    cursor: pointer;
    transition: color 0.2s;
    
    &:hover {
        color: $PRIMARY-PURPLE;
    }
}


// ------------------------------------
// SECCIÓN 1: TARJETAS DE RESUMEN (Componente TarjetaResumen.vue)
// ------------------------------------
.summary-cards-container {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 20px;
    margin-bottom: 40px;
}

.summary-card {
    padding: 20px;
    border-radius: 12px;
    display: flex;
    flex-direction: column;
    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.05);
    
    .icon-box {
        width: 40px;
        height: 40px;
        border-radius: 8px;
        display: flex;
        justify-content: center;
        align-items: center;
        color: white;
        font-size: 1.2rem;
        float: right; /* Alinea a la derecha para el diseño */
        margin-left: 10px;
    }
    .value {
        font-size: 1.8rem;
        font-weight: 700;
        margin-bottom: 0;
        clear: both; /* Limpia el float del icono */
    }
    .title {
        font-size: 0.9rem;
        color: $GRAY-COLD;
        margin-top: 5px;
    }
}

// ------------------------------------
// SECCIÓN 2: HEADER DE DISPOSITIVOS
// ------------------------------------
.dispositivos-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 25px;
    
    h2 {
        font-size: 1.5rem;
        font-weight: 600;
    }
    
    .actions-group {
        display: flex;
        gap: 15px;
    }
}
.form-control-search {
    padding: 8px 12px;
    border-radius: 8px;
    border: 1px solid #ccc;
    // Estilos adaptados en el tema
}
.btn-add-device {
    background-color: $SUCCESS-COLOR;
    color: white;
    border: none;
    padding: 8px 15px;
    border-radius: 8px;
    font-weight: 600;
    cursor: pointer;
    box-shadow: 0 3px 6px rgba($SUCCESS-COLOR, 0.3);
    i { margin-right: 5px; }
}
.actions-group {
    display: flex; gap: 10px; align-items: center;
    
    .search-box {
        position: relative;
        input {
            padding: 8px 10px 8px 35px; border-radius: 20px; border: 1px solid #ddd;
            font-size: 0.9rem; width: 200px; transition: width 0.3s;
            &:focus { width: 250px; border-color: #8A2BE2; }
        }
        i { position: absolute; left: 12px; top: 50%; transform: translateY(-50%); color: #999; }
    }
}
.pagination-controls {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 20px;
    margin-top: 40px;
    padding-bottom: 20px;
    
    .btn-page {
        background-color: transparent;
        border: 1px solid #8A2BE2;
        color: #8A2BE2;
        padding: 8px 16px;
        border-radius: 8px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s;
        display: flex;
        align-items: center;
        gap: 5px;
        
        &:hover:not(:disabled) {
            background-color: #8A2BE2;
            color: white;
        }
        &:disabled {
            border-color: #ccc;
            color: #ccc;
            cursor: not-allowed;
        }
    }
    
    .page-info {
        font-weight: 500;
        color: #99A2AD;
    }
}
// ------------------------------------
// SECCIÓN 3: GRID DE DISPOSITIVOS
// ------------------------------------
.dispositivos-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 20px;
}

// ------------------------------------
// ESTILOS DE TEMA (MODO CLARO/OSCURO)
// ------------------------------------

// MODO CLARO (Default)
.theme-light {
    background-color: $WHITE-SOFT;
    color: $DARK-TEXT;
    
    .btn-back { color: $DARK-TEXT; }
    
    .summary-card {
        background-color: $SUBTLE-BG-LIGHT;
    }
    .form-control-search {
        background-color: $SUBTLE-BG-LIGHT;
        border-color: #ddd;
        color: $DARK-TEXT;
    }
}

// MODO OSCURO
.theme-dark {
    background-color: $DARK-BG-CONTRAST; 
    color: $LIGHT-TEXT;
    
    .btn-back { color: $LIGHT-TEXT; }
    .dispositivos-header h2 { color: $LIGHT-TEXT; }
    
    .summary-card {
        background-color: $BLUE-MIDNIGHT;
        box-shadow: 0 6px 15px rgba(0, 0, 0, 0.2);
    }
    .summary-card .title {
        color: $GRAY-COLD;
    }
    
    .form-control-search {
        background-color: $BLUE-MIDNIGHT;
        border-color: rgba($LIGHT-TEXT, 0.2);
        color: $LIGHT-TEXT;
    }
}
</style>