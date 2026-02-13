<template>
  <div class="plataforma-layout" :class="{ 'theme-dark': isDark, 'theme-light': !isDark }">
    
    <BarraLateralPlataforma :is-open="isSidebarOpen" />
    
    <div class="plataforma-contenido" :class="{ 'shifted': isSidebarOpen }">
      
      <EncabezadoPlataforma 
        :titulo="'Gestión de Campos (' + (sensor.nombre || 'Cargando...') + ')'"
        :subtitulo="'Sensor Tipo: ' + (sensor.tipo || 'N/A') + ' | Dispositivo ID: ' + (sensor.dispositivo_id || 'N/A')"
        @toggle-sidebar="toggleSidebar" 
        :is-sidebar-open="isSidebarOpen"
      >
        <template #title-prefix>
            <button @click="goBack" class="btn-back" title="Volver al Dispositivo">
                <i class="bi bi-arrow-left-circle-fill"></i>
            </button>
        </template>
      </EncabezadoPlataforma>

     <div class="campos-detalle-contenido">
    <div v-if="loading" class="alert-info">Cargando campos...</div>
    <div v-else-if="error" class="alert-error">{{ error }}</div>
    <div v-else>
        
        <div class="campos-header">
            <h3>Campos Registrados ({{ campos.length }})</h3>
           <button 
                v-if="puedeEditar" 
                @click="openCreateCampoModal" 
                class="btn-primary-action"
            >
                <i class="bi bi-plus-circle-fill"></i> Crear Campo
            </button>
        </div>
        
       <div class="campos-grid">
<TarjetaCampoSensor
    v-for="campo in campos"
    :key="campo.id"
    :campo="campo"
    :is-dark="isDark"
    :rol="rolUsuario"  
    :editable="puedeEditar"
    @edit-campo="openEditCampoModal"
    @delete-campo="confirmarEliminacionCampo"
/>
</div>
        
        <div v-if="campos.length === 0" class="alert-empty-data">
            Este sensor no tiene campos de medición registrados.
        </div>
    </div>
</div>
    </div>
    <ModalCampoSensor 
        v-if="mostrarModalCrearCampo"
        :modo-edicion="false"
        :sensor-id="sensorId"
        @campo-guardado="handleCampoGuardado"
        @close="closeCreateCampoModal"
    />
    
    <ModalCampoSensor 
        v-if="mostrarModalEditarCampo"
        :modo-edicion="true"
        :sensor-id="sensorId"
        :campo-data="campoSeleccionado" 
        @campo-guardado="handleCampoGuardado"
        @close="closeEditCampoModal"
    />
    <ModalEliminarBase 
    v-if="mostrarModalEliminarCampo"
    titulo="Confirmar Eliminación"
    :is-dark="isDark"
    :mensaje="'¿Estás seguro de que deseas eliminar el campo \'' + campoEliminarNombre + '\'?'"
    @cancelar="cancelarEliminacionCampo"
    @confirmar="ejecutarEliminacionCampo"
/>
    </div>
</template>

<script>
// Componentes de Layout
import BarraLateralPlataforma from '../plataforma/BarraLateralPlataforma.vue';
import EncabezadoPlataforma from '../plataforma/EncabezadoPlataforma.vue';

import ModalCampoSensor from './ModalCampoSensor.vue';
import TarjetaCampoSensor from './TarjetaCampoSensor.vue';
import ModalEliminarBase from './ModalEliminarBase.vue';


export default {
    name: 'DetalleSensor',
    components: {
        BarraLateralPlataforma,
        EncabezadoPlataforma,
        TarjetaCampoSensor,
        ModalCampoSensor,
        ModalEliminarBase,
    },

    data() {
        return {
            isDark: false,
            isSidebarOpen: true,
            loading: true,
            error: null,

            dispositivoIdPadre: null,
            sensor: {},
            campos: [],

            mostrarModalCrearCampo: false,
            mostrarModalEditarCampo: false,
            campoSeleccionado: null,

            mostrarModalEliminarCampo: false,
            campoEliminarId: null,
            campoEliminarNombre: null,

            rolUsuario: null,   // <-- Aquí guardaremos el rol REAL
                    rol: null,   // 🔥 ahora sí existe para pasar al hijo

            pollingInterval: null
        };
    },

    computed: {
        sensorId() {
            return this.$route.params.id;
        },

        // Ahora sí funciona con los valores reales del backend
        puedeEditar() {
            return (
                this.rolUsuario === 'PROPIETARIO' ||
                this.rolUsuario === 'COLABORADOR'|| this.rolUsuario === 'Colaborador' || this.rolUsuario === 'Propietario'
            );
        }
    },

    mounted() {
        this.cargarDetalles();
        this.detectarTemaSistema();

        if (window.matchMedia) {
            window.matchMedia('(prefers-color-scheme: dark)')
                .addEventListener('change', this.handleThemeChange);
        }

        this.pollingInterval = setInterval(() => {
            this.cargarCampos();
        }, 10000);
    },

    beforeUnmount() {
        if (window.matchMedia) {
            window.matchMedia('(prefers-color-scheme: dark)')
                .removeEventListener('change', this.handleThemeChange);
        }
        if (this.pollingInterval) clearInterval(this.pollingInterval);
    },

    methods: {
        async cargarDetalles() {
            this.loading = true;
            this.error = null;

            const token = localStorage.getItem('accessToken');
            if (!token || !this.sensorId) {
                this.$router.push('/');
                return;
            }

            try {
                const sensorResponse = await fetch(
                    `${API_BASE_URL}/api/sensores/${this.sensorId}`,
                    { headers: { Authorization: `Bearer ${token}` } }
                );

                if (!sensorResponse.ok) throw new Error('Sensor no encontrado.');
                this.sensor = await sensorResponse.json();
                this.dispositivoIdPadre = this.sensor.dispositivo_id;

                const camposResponse = await fetch(
                    `${API_BASE_URL}/api/sensores/${this.sensorId}/campos`,
                    { headers: { Authorization: `Bearer ${token}` } }
                );

                if (!camposResponse.ok) throw new Error('Fallo al obtener campos.');

                const responseJSON = await camposResponse.json();
                const camposRaw = responseJSON.campos || [];

                this.campos = camposRaw.map(c => ({
                    id: c.id,
                    nombre: c.nombre,
                    tipo_valor: c.tipo_valor,
                    simbolo_unidad: c.simbolo_unidad || "",
                    magnitud_tipo: c.magnitud_tipo || "",
                    ultimo_valor: c.ultimo_valor ?? "N/A",
                    fecha_ultimo_valor: c.fecha_ultimo_valor || null
                }));

                // 🔥 CORREGIDO: antes guardabas this.rol
                this.rolUsuario = responseJSON.rol;

            } catch (err) {
                this.error = err.message || 'Error al cargar los detalles.';
            } finally {
                this.loading = false;
            }
        },

        async cargarCampos() {
                    const token = localStorage.getItem('accessToken');
                    if (!token || !this.sensorId) return;

                    try {
                        const camposResponse = await fetch(
                            `${API_BASE_URL}/api/sensores/${this.sensorId}/campos`,
                            { headers: { Authorization: `Bearer ${token}` } }
                        );

                        if (!camposResponse.ok) return;

                        const responseJSON = await camposResponse.json();

                        // 🔥 Guardamos el rol del backend
                        this.rol = responseJSON.rol;

                        const camposRaw = responseJSON.campos || [];

                        this.campos = camposRaw.map(c => ({
                            id: c.id,
                            nombre: c.nombre,
                            tipo_valor: c.tipo_valor,
                            simbolo_unidad: c.simbolo_unidad || "",
                            magnitud_tipo: c.magnitud_tipo || "",
                            ultimo_valor: c.ultimo_valor ?? "N/A",
                            fecha_ultimo_valor: c.fecha_ultimo_valor || null
                        }));

                    } catch (err) {
                        console.warn("Error en polling:", err.message);
                    }
                },


        // ---------------------- OTROS MÉTODOS ----------------------

        goBack() {
            if (this.dispositivoIdPadre) {
                this.$router.push(`/detalle-dispositivo/${this.dispositivoIdPadre}`);
            } else {
                this.$router.back();
            }
        },

        toggleSidebar() {
            this.isSidebarOpen = !this.isSidebarOpen;
        },

        openCreateCampoModal() {
            this.mostrarModalCrearCampo = true;
        },

        closeCreateCampoModal() {
            this.mostrarModalCrearCampo = false;
        },

        openEditCampoModal(campo) {
            this.campoSeleccionado = campo;
            this.mostrarModalEditarCampo = true;
        },

        closeEditCampoModal() {
            this.mostrarModalEditarCampo = false;
            this.campoSeleccionado = null;
        },

        confirmarEliminacionCampo(id, nombre) {
            this.campoEliminarId = id;
            this.campoEliminarNombre = nombre;
            this.mostrarModalEliminarCampo = true;
        },

        cancelarEliminacionCampo() {
            this.mostrarModalEliminarCampo = false;
            this.campoEliminarId = null;
            this.campoEliminarNombre = null;
        },

        async ejecutarEliminacionCampo() {
            this.loading = true;
            const token = localStorage.getItem('accessToken');

            try {
                const response = await fetch(
                    `${API_BASE_URL}/api/campos_sensores/${this.campoEliminarId}`,
                    { method: 'DELETE', headers: { Authorization: `Bearer ${token}` } }
                );

                const data = await response.json();
                if (!response.ok) throw new Error(data.detail || 'Fallo al eliminar.');

                alert('Campo eliminado exitosamente.');
                this.cancelarEliminacionCampo();
                this.cargarDetalles();

            } catch (err) {
                alert('Error al eliminar: ' + err.message);
                this.cancelarEliminacionCampo();
            } finally {
                this.loading = false;
            }
        },

        handleCampoGuardado() {
            this.closeCreateCampoModal();
            this.closeEditCampoModal();
            this.cargarDetalles();
        },

        handleThemeChange(event) {
            this.isDark = event.matches;
        },

        detectarTemaSistema() {
            this.isDark = window.matchMedia &&
                window.matchMedia('(prefers-color-scheme: dark)').matches;
        }
    }
};
</script>


<style scoped lang="scss">
// ----------------------------------------
// VARIABLES SCSS (Mínimas para el Layout)
// ----------------------------------------
// $WIDTH-SIDEBAR: 280px; 
// $WIDTH-CLOSED: 80px; 
// $WHITE-SOFT: #F7F9FC; 
// $DARK-BG-CONTRAST: #1E1E30; 
// $LIGHT-TEXT: #E4E6EB;
// $DARK-TEXT: #333333;
// $SUBTLE-BG-DARK: #2B2B40; 
// $PRIMARY-PURPLE: #8A2BE2;
// $SUCCESS-COLOR: #1ABC9C;
// $GRAY-COLD: #99A2AD;
// $BLUE-MIDNIGHT: #1A1A2E; 

// // ----------------------------------------
// // LAYOUT Y POSICIONAMIENTO
// // ----------------------------------------
// .plataforma-layout {
//     display: flex;
//     min-height: 100vh;
//     transition: background-color 0.3s;
//     background-color: $WHITE-SOFT; 
// }

// .plataforma-contenido {
//     margin-left: $WIDTH-CLOSED;
//     flex-grow: 1;
//     padding: 0; 
//     transition: margin-left 0.3s ease-in-out;
//     &.shifted { margin-left: $WIDTH-SIDEBAR; }
// }

.campos-detalle-contenido {
    padding: 20px 40px 40px 40px;
}

// Estilo del botón Volver
.btn-back {
    background: none; border: none;
    color: $DARK-TEXT;
    font-size: 1.4rem;
    margin-right: 15px;
    cursor: pointer;
    transition: color 0.2s;
    &:hover { color: $PRIMARY-PURPLE; }
}

// ----------------------------------------
// ESTILOS DE LA TABLA Y HEADER
// ----------------------------------------
.campos-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    
    h3 { font-size: 1.4rem; font-weight: 600; }
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

.campos-tabla-container {
    width: 100%;
    border-radius: 10px;
    overflow: hidden;
    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
}
.campos-grid {
    display: grid;
    /* Columnas auto-ajustables */
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); 
    gap: 20px;
}
.table {
    width: 100%;
    margin-bottom: 0;
    
    th {
        font-size: 0.9rem;
        text-transform: uppercase;
        padding: 15px;
        color: $GRAY-COLD;
        background-color: $BLUE-MIDNIGHT; 
    }
    
    td {
        padding: 12px 15px;
        font-size: 0.95rem;
    }
    
    .simbolo-badge {
        font-weight: bold;
        padding: 4px 8px;
        border-radius: 4px;
        background-color: $PRIMARY-PURPLE;
        color: white;
    }
    
    .btn-action {
        background: none; border: none;
        color: $GRAY-COLD;
        font-size: 1rem;
        margin-left: 10px;
        &:hover { color: $PRIMARY-PURPLE; }
    }
}

// ----------------------------------------
// TEMAS (REACTIVIDAD Y MODO OSCURO)
// ----------------------------------------

.theme-light {
    background-color: $WHITE-SOFT; 
    color: $DARK-TEXT;
    .btn-back { color: $DARK-TEXT; }
    .table { border: 1px solid #ddd; background-color: #fff; }
    .table td { color: $DARK-TEXT; border-color: #eee; }
}

.theme-dark {
    background-color: $DARK-BG-CONTRAST; 
    color: $LIGHT-TEXT;
    
    .btn-back { color: $LIGHT-TEXT; }
    .plataforma-contenido { background-color: $DARK-BG-CONTRAST; }
    .campos-header h3 { color: $LIGHT-TEXT; }

    .table {
        background-color: $SUBTLE-BG-DARK;
        color: $LIGHT-TEXT;
        border: 1px solid rgba($LIGHT-TEXT, 0.1);
        
        th { background-color: $BLUE-MIDNIGHT; color: $GRAY-COLD; border-bottom-color: rgba($LIGHT-TEXT, 0.1); }
        
        td { color: $LIGHT-TEXT !important; border-color: rgba($LIGHT-TEXT, 0.05); } 
        
        .table-striped > tbody > tr:nth-of-type(odd) > td {
            background-color: $BLUE-MIDNIGHT !important; 
        }
        .table-striped > tbody > tr:nth-of-type(even) > td {
            background-color: $SUBTLE-BG-DARK !important; 
        }
        .table-hover > tbody > tr:hover > td {
             background-color: rgba($LIGHT-TEXT, 0.1) !important;
        }
    }
    
    .btn-action { color: $GRAY-COLD; }
    
    .alert-empty-data {
        background-color: rgba($PRIMARY-PURPLE, 0.1);
        color: $PRIMARY-PURPLE;
    }
}
</style>