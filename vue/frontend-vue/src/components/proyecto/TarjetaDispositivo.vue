<template>
    <div 
        class="tarjeta-dispositivo" 
        :class="{ 
            'theme-dark': isDark, 
            'theme-light': !isDark,
            'disabled': !dispositivo.habilitado 
        }"
    >
        <div class="tarjeta-header">
            <div class="icon-and-name">
                <i :class="getDeviceIcon(dispositivo.tipo)" class="dispositivo-icono"></i>
                
                <div class="name-type-group">
                    <span class="dispositivo-tipo-badge">{{ dispositivo.tipo || 'General' }}</span>
                    <!-- Enlace al detalle del dispositivo (si existe la ruta) -->
                    <router-link 
                        v-if="dispositivo.id"
                        :to="{ name: 'DetalleDispositivo', params: { id: dispositivo.id } }" 
                        class="link-detalle"
                    >
                        <h3 class="dispositivo-nombre">{{ dispositivo.nombre || 'Cargando...' }}</h3>
                    </router-link>
                    <h3 v-else class="dispositivo-nombre">{{ dispositivo.nombre || 'Cargando...' }}</h3>
                </div>
            </div>
            
            <i :class="dispositivo.habilitado ? 'bi bi-wifi' : 'bi bi-wifi-off'" class="wifi-signal"></i>
        </div>
        
        <p class="dispositivo-descripcion">{{ dispositivo.descripcion || 'Sin descripción detallada.' }}</p>

        <div class="dispositivo-info">
            <span class="info-item porcentaje-carga">
                <i :class="getBatteryIcon(dispositivo.porcentaje_carga)"></i> 
                {{ dispositivo.porcentaje_carga || 0 }}%
            </span>
            <span v-if="dispositivo.latitud" class="info-item ubicacion">
                <i class="bi bi-geo-alt-fill"></i> 
                {{ dispositivo.latitud }}, {{ dispositivo.longitud }}
            </span>
        </div>

        <p class="dispositivo-ultima-lectura">Visto: {{ dispositivo.ultima_lectura || 'N/A' }}</p>

        <div class="tarjeta-footer">
            <div class="habilitado-switch">
                <label class="toggle-switch">
                    <input 
                        type="checkbox" 
                        :checked="dispositivo.habilitado" 
                        @change="toggleHabilitado(dispositivo.id)"
                        :disabled="!puedeEditar" 
                    >
                    <span class="slider round" :class="{ 'disabled-slider': !puedeEditar }"></span>
                </label>
                <span class="label-text">{{ dispositivo.habilitado ? 'Habilitado' : 'Deshabilitado' }}</span>
            </div>

            <div class="acciones">
                <!-- 🚨 RENDERIZADO CONDICIONAL BASADO EN ROL -->
                <template v-if="puedeEditar">
                    <button @click="editDevice()" class="btn-accion" title="Editar Dispositivo">
                        <i class="bi bi-pencil"></i>
                    </button>
                    <button @click="deleteDevice(dispositivo.id)" class="btn-accion btn-delete" title="Eliminar Dispositivo">
                        <i class="bi bi-trash"></i>
                    </button>
                </template>
                <!-- Opcional: Icono de candado si no tiene permisos -->
                <span v-else class="rol-badge-small" title="Modo Solo Lectura">
                   <i class="bi bi-eye"></i>
                </span>
            </div>
        </div>
    </div>
</template>

<script>
export default {
    name: 'TarjetaDispositivo',
    props: {
        dispositivo: {
            type: Object,
            default: () => ({ 
                id: null,
                nombre: 'Error de Carga', 
                tipo: 'Sensor', 
                descripcion: '',
                habilitado: false, 
                porcentaje_carga: 0,
                ultima_lectura: 'N/A',
                latitud: null,
                longitud: null,
                mi_rol: '' // Fallback si viene en el objeto
            })
        },
        isDark: {
            type: Boolean,
            required: true
        },
        miRol: {
            type: String,
            default: ''
        }
    },
    emits: ['edit-device', 'open-delete-modal', 'toggle-habilitado'],
    computed: {
        puedeEditar() {
            // Priorizamos el prop miRol, si no existe usamos el del objeto dispositivo
            const rol = (this.miRol || this.dispositivo.mi_rol || '').toUpperCase();
            return rol === 'PROPIETARIO' ||rol=== 'Propietario'|| rol=== 'Colaborador'  || rol === 'COLABORADOR' || rol === 'EDITOR';
        }
    },
    methods: {
        toggleHabilitado(id) {
            if (!this.puedeEditar) return; // Doble protección
            this.$emit('toggle-habilitado', id, !this.dispositivo.habilitado); 
        },
        getBatteryIcon(percentage) {
            if (percentage >= 90) return 'bi bi-battery-full';
            if (percentage >= 60) return 'bi bi-battery-three-quarters';
            if (percentage >= 30) return 'bi bi-battery-half';
            if (percentage > 10) return 'bi bi-battery-quarter';
            return 'bi bi-battery';
        },
        getDeviceIcon(type) {
             if (!type || typeof type !== 'string') return 'bi bi-tablet';
             switch (type.toLowerCase()) {
                case 'sensor': return 'bi bi-thermometer-sun'; 
                case 'actuador': return 'bi bi-lightbulb';
                case 'controlador': return 'bi bi-sliders'; 
                case 'microcontrolador': return 'bi bi-cpu';
                case 'raspberry pi': return 'bi bi-motherboard-fill';
                default: return 'bi bi-tablet';
            }
        },
        editDevice() {
            this.$emit('edit-device', this.dispositivo);
        },
        deleteDevice(id) {
            this.$emit('open-delete-modal', id, this.dispositivo.nombre);
        }
    }
}
</script>

<style scoped lang="scss">

@use "sass:color";
// ----------------------------------------
// BASE DE LA TARJETA
// ----------------------------------------
.tarjeta-dispositivo {
    background-color: $WHITE-SOFT;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
    display: flex;
    flex-direction: column;
    transition: all 0.3s ease;
    border: 1px solid transparent; 
    position: relative; 
    
    &:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 16px rgba(0, 0, 0, 0.12);
    }
    
    &.disabled {
        opacity: 0.8; 
        /* filter: grayscale(10%); Quitamos grayscale total para que se vea mejor */
    }

    .tarjeta-header {
        display: flex;
        align-items: flex-start; 
        justify-content: space-between;
        margin-bottom: 5px; 
        
        .icon-and-name {
            display: flex;
            align-items: flex-start; 
            flex-grow: 1;

            .dispositivo-icono {
                font-size: 1.5rem;
                color: $SUCCESS-COLOR; 
                margin-right: 10px;
                margin-top: 5px; 
            }
            
            .name-type-group {
                display: flex;
                flex-direction: column; 
                align-items: flex-start;
                margin-top: 0;
            }
        }
        
        .link-detalle {
            text-decoration: none;
            color: inherit;
            &:hover .dispositivo-nombre { color: $PRIMARY-PURPLE; }
        }

        .dispositivo-nombre {
            font-size: 1.15rem;
            font-weight: 600;
            margin: 0;
            line-height: 1.2;
            transition: color 0.2s;
        }
        .wifi-signal {
            font-size: 1.2rem;
            color: $SUCCESS-COLOR;
            margin-left: 10px;
        }
    }
    
    .dispositivo-tipo-badge {
        position: static; 
        background-color: rgba($PRIMARY-PURPLE, 0.1); 
        color: $PRIMARY-PURPLE;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
        border: 1px solid rgba($PRIMARY-PURPLE, 0.3);
        margin-bottom: 4px; 
        order: -1; 
    }
    
    .dispositivo-descripcion {
        font-size: 0.9rem;
        color: $GRAY-COLD;
        margin-bottom: 10px; 
        margin-top: 5px; 
        height: 38px;
        overflow: hidden;
        display: -webkit-box;
        line-clamp: 2;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
    }

    .dispositivo-info {
        display: flex;
        justify-content: space-between;
        margin-bottom: 15px;
        padding: 8px 0;
        border-top: 1px solid rgba(0, 0, 0, 0.05);
        font-size: 0.9rem;
        
        .info-item {
            display: flex;
            align-items: center;
            gap: 5px;
            i { font-size: 1rem; }
            &.porcentaje-carga { color: $SUCCESS-COLOR; }
            &.ubicacion { color: $GRAY-COLD; }
        }
    }

    .dispositivo-ultima-lectura {
        font-size: 0.8rem;
        color: $GRAY-COLD;
        margin-bottom: 20px;
        padding-top: 5px;
    }
}

// ----------------------------------------
// FOOTER Y ACCIONES
// ----------------------------------------
.tarjeta-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-top: 15px;
    border-top: 1px solid rgba(0, 0, 0, 0.05);
}

.habilitado-switch {
    display: flex;
    align-items: center;
    gap: 10px;
    span.label-text { font-size: 0.9rem; font-weight: 500; }
}

.acciones {
    display: flex;
    gap: 8px;
    align-items: center;
    
    .rol-badge-small {
        color: $GRAY-COLD;
        font-size: 1.2rem;
        opacity: 0.5;
    }

    .btn-accion {
        padding: 6px; 
        border-radius: 50%;
        cursor: pointer; transition: color 0.2s, background-color 0.2s;
        font-size: 0.95rem;
        color: $GRAY-COLD;
        background: none; 
        border: none;
        
        &:hover { background-color: rgba($GRAY-COLD, 0.1); color: $PRIMARY-PURPLE; }
        &.btn-delete:hover { color: $DANGER-COLOR; }
    }
}

// ----------------------------------------
// ESTILOS DEL SWITCH (Toggle)
// ----------------------------------------
.toggle-switch {
    position: relative;
    display: flex;
    align-items: center;
    cursor: pointer;
    user-select: none;
    
    input { opacity: 0; width: 0; height: 0; }

    .slider {
        position: relative; width: 40px; height: 20px;
        background-color: $INACTIVE-COLOR; 
        transition: 0.4s;
        border-radius: 20px;
        
        &.disabled-slider {
            opacity: 0.5;
            cursor: not-allowed;
        }
    }
    .slider:before {
        position: absolute; content: ""; height: 16px; width: 16px;
        left: 2px; bottom: 2px; background-color: #fff;
        transition: 0.4s; border-radius: 50%;
    }

    input:checked + .slider { background-color: $SUCCESS-COLOR; }
    input:checked + .slider:before { transform: translateX(20px); }
    
    .label-text { color: $DARK-TEXT; }
}

// ----------------------------------------
// TEMAS (DARK/LIGHT)
// ----------------------------------------
.theme-light {
    background-color: $WHITE-SOFT;
    color: $DARK-TEXT;
    border-color: #f0f0f0;
    .dispositivo-nombre { color: $DARK-TEXT; }
    .tarjeta-footer { border-top-color: rgba($DARK-TEXT, 0.05); }
    .dispositivo-ultima-lectura { border-top-color: rgba($DARK-TEXT, 0.1); }
    .dispositivo-tipo-badge {
        background-color: rgba($PRIMARY-PURPLE, 0.1);
        color: $PRIMARY-PURPLE;
        border-color: rgba($PRIMARY-PURPLE, 0.3);
    }
}

.theme-dark {
    background-color: $SUBTLE-BG-DARK;
    color: $LIGHT-TEXT;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    border-color: rgba($LIGHT-TEXT, 0.1);
    
    .dispositivo-icono { color: $SUCCESS-COLOR; }
    .dispositivo-nombre { color: $LIGHT-TEXT; }
    .dispositivo-descripcion, .dispositivo-ultima-lectura, .dispositivo-info .ubicacion { color: $GRAY-COLD; }
    .tarjeta-footer { border-top-color: rgba($LIGHT-TEXT, 0.1); }
    
    .acciones .btn-accion { 
        color: $GRAY-COLD; 
        &:hover { background-color: rgba($LIGHT-TEXT, 0.05); color: $PRIMARY-PURPLE; }
        &.btn-delete:hover { color: $DANGER-COLOR; }
    }
    
    .dispositivo-tipo-badge {
        background-color: rgba($PRIMARY-PURPLE, 0.3);
        color: $LIGHT-TEXT;
        border-color: rgba($PRIMARY-PURPLE, 0.5);
    }
}
</style>