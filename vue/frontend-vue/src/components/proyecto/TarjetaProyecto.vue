<template>
    <div 
        class="proyecto-tarjeta" 
        :class="{ 'theme-dark': isDark, 'theme-light': !isDark, 'active': proyecto.activo }"
        @click="irAlDetalle"
    >
        <div class="card-header">
            <div class="icon-box" :style="{ background: iconGradient }">
                <i :class="proyecto.icono || 'bi bi-box-seam'"></i>
            </div>
            
            <!-- Indicador de estado visual -->
            <span class="status-dot" :class="{ 'online': proyecto.activo, 'offline': !proyecto.activo }"></span>
        </div>

        <div class="card-body">
            <h2 class="proyecto-titulo">{{ proyecto.nombre }}</h2>
            
            <p class="proyecto-tipo-estado">
                <span class="tag-tipo">{{ proyecto.tipo_industria || 'General' }}</span> 
                <span class="tag-estado" :class="proyecto.activo ? 'text-active' : 'text-inactive'">
                    {{ statusText }}
                </span>
            </p>
            
            <p class="proyecto-descripcion">{{ proyecto.descripcion || 'Sin descripción disponible.' }}</p>
            
            <div class="metricas-container">
                <div class="metrica metrica-dispositivos">
                    <i class="bi bi-tablet"></i>
                    <span>Dispositivos</span>
                    <!-- Usamos valores seguros para evitar NaN -->
                    <span class="count">{{ proyecto.dispositivos_count || 0 }}</span>
                </div>
                
                <div class="metrica metrica-sensores">
                    <i class="bi bi-activity"></i>
                    <span>Sensores</span>
                    <span class="count">{{ proyecto.sensores_count || 0 }}</span>
                </div>
            </div>
            
            <div class="card-footer">
                <span class="ultima-actualizacion">
                    <i class="bi bi-clock"></i> 
                    <span class="time-ago">{{ proyecto.ultima_actualizacion || 'Reciente' }}</span>
                </span>
                
                <div class="acciones">
                    <!-- BADGE DEL ROL -->
                    <span class="role-badge" :class="claseRol">
                        {{ proyecto.mi_rol }}
                    </span>

                    <!-- BOTÓN PAUSAR/ACTIVAR (Propietario y Colaborador) -->
                    <button 
                        v-if="esPropietario || esColaborador"
                        @click.stop="toggleState" 
                        class="btn-accion btn-toggle-state" 
                        :class="{'btn-pause': proyecto.activo}" 
                        :title="toggleAction"
                    >
                        <i :class="toggleIcon"></i>
                    </button>
                    
                    <!-- 🚨 ZONA PROTEGIDA: SOLO PROPIETARIO -->
                    <template v-if="esPropietario">
                        <button 
                            class="btn-accion btn-share" 
                            @click.stop="openShareModal" 
                            title="Invitar usuarios"
                        >
                            <i class="bi bi-share-fill"></i>
                        </button>
                        
                        <button 
                            class="btn-accion btn-detalle" 
                            @click.stop="editProject" 
                            title="Editar proyecto"
                        >
                            <i class="bi bi-pencil-fill"></i>
                        </button>

                        <button 
                            class="btn-accion btn-eliminar" 
                            @click.stop="deleteProject" 
                            title="Eliminar proyecto"
                        >
                            <i class="bi bi-trash-fill"></i>
                        </button>
                    </template>
                </div>
            </div>
        
        </div>
    </div>
</template>

<script>
// Colores para los gradientes de los iconos
const PROJECT_COLORS = [
    'linear-gradient(135deg, #8A2BE2, #6F00FF)', // Purple
    'linear-gradient(135deg, #1ABC9C, #00C853)', // Green
    'linear-gradient(135deg, #FFC107, #FF8C00)', // Orange
    'linear-gradient(135deg, #3498db, #2980b9)', // Blue
    'linear-gradient(135deg, #E74C3C, #c0392b)', // Red
];

const getColorForId = (id) => {
    if (!id) return PROJECT_COLORS[0];
    return PROJECT_COLORS[id % PROJECT_COLORS.length];
};

export default {
    name: 'TarjetaProyecto',
    props: {
        proyecto: {
            type: Object,
            required: true,
            default: () => ({
                id: 0,
                nombre: 'Sin Nombre',
                descripcion: '',
                activo: true,
                mi_rol: 'OBSERVADOR'
            })
        },
        isDark: {
            type: Boolean,
            required: true
        }
    },
    emits: ['toggle-activo', 'open-share-modal', 'edit-project', 'confirmar-eliminar'],
    computed: {
        // Lógica de Roles Segura (Case Insensitive)
        rolNormalizado() {
            return (this.proyecto.mi_rol || '').toUpperCase();
        },
        esPropietario() {
            return this.rolNormalizado === 'PROPIETARIO' || this.rolNormalizado === 'Propietario';
        },
        esColaborador() {
            return this.rolNormalizado === 'COLABORADOR'|| this.rolNormalizado === 'Colaborador';
        },

        claseRol() {
            if (this.esPropietario) return 'badge-owner';
            if (this.esColaborador) return 'badge-collab';
            return 'badge-guest';
        },
        
        // Lógica Visual
        iconGradient() {
            return getColorForId(this.proyecto.id);
        },
        toggleAction() {
            return this.proyecto.activo ? 'Pausar' : 'Activar';
        },
        toggleIcon() {
            return this.proyecto.activo ? 'bi bi-pause-fill' : 'bi bi-play-fill';
        },
        statusText() {
            return this.proyecto.activo ? 'Activo' : 'Pausado';
        }
    },
    methods: {
        irAlDetalle() {
            this.$router.push({ name: 'DetalleProyecto', params: { id: this.proyecto.id } });
        },
        toggleState() {
            this.$emit('toggle-activo', this.proyecto.id); 
        },
        openShareModal() {
            this.$emit('open-share-modal', this.proyecto.id); 
        },
        editProject() {
            // Solo se emite si es propietario (doble seguridad visual)
            if (this.esPropietario) {
this.$emit('edit-project', this.proyecto);            }
        },
        deleteProject() {
            if (this.esPropietario) {


                this.$emit('confirmar-eliminar', this.proyecto);            }
        }
    }
}
</script>

<style scoped lang="scss">
// 1. IMPORTAR MÓDULO DE COLOR (Necesario para color.adjust)
@use "sass:color";

// ----------------------------------------
// TARJETA BASE
// ----------------------------------------
.proyecto-tarjeta {
    border-radius: 16px; 
    padding: 24px; 
    padding-bottom: 35px; 
    margin-bottom: 20px;
    transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
    cursor: pointer;
    display: flex;
    flex-direction: column;
    border: 1px solid transparent;
    position: relative;
    overflow: hidden;

    &:hover {
        transform: translateY(-5px);
    }
}

// ----------------------------------------
// CABECERA E ICONO
// ----------------------------------------
.card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 15px;
}

.icon-box {
    width: 48px; height: 48px; 
    border-radius: 12px;
    display: flex; justify-content: center; align-items: center;
    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.15);
    
    i { 
        font-size: 1.5rem; 
        color: $WHITE;
    }
}

.status-dot { 
    width: 10px; height: 10px;
    border-radius: 50%;
    background-color: $GRAY-COLD;
    
    &.online { background-color: $SUCCESS-COLOR; box-shadow: 0 0 8px rgba($SUCCESS-COLOR, 0.6); }
    &.offline { background-color: $WARNING-COLOR; }
}

// ----------------------------------------
// CUERPO
// ----------------------------------------
.card-body {
    flex: 1;
    display: flex;
    flex-direction: column;
}

.proyecto-titulo { 
    font-size: 1.3rem; 
    font-weight: 700; 
    margin-bottom: 8px; 
    line-height: 1.2;
}

.proyecto-tipo-estado {
    font-size: 0.85rem; 
    margin-bottom: 15px;
    display: flex;
    align-items: center;
    gap: 8px;
    
    .tag-tipo {
        font-weight: 600; 
        color: $PRIMARY-PURPLE;
        text-transform: uppercase;
        font-size: 0.75rem;
        letter-spacing: 0.5px;
    }
    
    .tag-estado {
        font-weight: 500;
        padding-left: 8px;
        border-left: 1px solid $GRAY-COLD;
        
        &.text-active { color: $SUCCESS-COLOR; }
        &.text-inactive { color: $WARNING-COLOR; }
    }
}

.proyecto-descripcion {
    font-size: 0.9rem; 
    margin-bottom: 20px;
    line-height: 1.5;
    height: 2.8em;
    overflow: hidden;
    text-overflow: ellipsis;
    display: -webkit-box;
    line-clamp: 2;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    opacity: 0.8;
}

// ----------------------------------------
// MÉTRICAS
// ----------------------------------------
.metricas-container {
    display: flex;
    gap: 12px;
    margin-bottom: 20px;
    
    .metrica {
        flex: 1;
        padding: 10px 12px;
        border-radius: 10px;
        display: flex;
        flex-direction: column;
        align-items: flex-start;
        transition: background-color 0.2s;
        border: 1px solid transparent;
        
        i { 
            font-size: 1.1rem; 
            margin-bottom: 6px;
            color: $PRIMARY-PURPLE; 
        }
        
        span:first-of-type { 
            font-size: 0.75rem;
            opacity: 0.8;
            margin-bottom: 2px;
            font-weight: 500;
        }
        
        .count {
            font-size: 1.4rem; 
            font-weight: 700;
            line-height: 1;
        }
    }
}

// ----------------------------------------
// FOOTER
// ----------------------------------------
.card-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-top: 20px; 
    border-top: 1px solid transparent;
    margin-top: auto;
    gap: 10px; 
    
    .ultima-actualizacion {
        font-size: 0.65rem; 
        color: $GRAY-COLD;
        display: flex;
        align-items: center;
        gap: 4px;
        flex-shrink: 0; 
        
        i { font-size: 0.8rem; }
        .time-ago { font-weight: 600; }
    }

    .acciones {
        display: flex;
        align-items: center;
        gap: 5px; 
        flex-shrink: 0; 
        
        .role-badge {
            font-size: 0.65rem;
            padding: 2px 6px;
            border-radius: 4px;
            font-weight: 700;
            text-transform: uppercase;
            margin-right: 4px;
            white-space: nowrap;
            
            &.badge-owner { background-color: rgba($SUCCESS-COLOR, 0.1); color: $SUCCESS-COLOR; border: 1px solid rgba($SUCCESS-COLOR, 0.2); }
            &.badge-collab { background-color: rgba($PRIMARY-PURPLE, 0.1); color: $PRIMARY-PURPLE; border: 1px solid rgba($PRIMARY-PURPLE, 0.2); }
            &.badge-guest { background-color: rgba($GRAY-COLD, 0.1); color: $GRAY-COLD; border: 1px solid rgba($GRAY-COLD, 0.2); }
        }

        .btn-accion {
            width: 32px; height: 32px;
            border-radius: 8px;
            border: none;
            background: transparent;
            display: flex; justify-content: center; align-items: center;
            cursor: pointer;
            transition: all 0.2s;
            font-size: 0.9rem;
            flex-shrink: 0;
            
            &:hover { transform: translateY(-2px); }
            
            &.btn-toggle-state {
                color: $LIGHT-TEXT; 
                &.btn-pause { background-color: rgba($WARNING-COLOR, 0.1); color: $WARNING-COLOR; }
                &:not(.btn-pause) { background-color: rgba($SUCCESS-COLOR, 0.1); color: $SUCCESS-COLOR; }
            }
            
            &.btn-share { color: $PRIMARY-PURPLE; background-color: rgba($PRIMARY-PURPLE, 0.1); }
            &.btn-detalle { color: $GRAY-COLD; background-color: rgba($GRAY-COLD, 0.1); &:hover { color: $PRIMARY-PURPLE; } }
            &.btn-eliminar { color: $DANGER-COLOR; background-color: rgba($DANGER-COLOR, 0.1); }
        }
    }
}

// ----------------------------------------
// TEMAS
// ----------------------------------------
.theme-light {
    background-color: $WHITE-SOFT;
    box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    
    .proyecto-titulo { color: $DARK-TEXT; }
    .proyecto-descripcion { color: $DARK-TEXT; }
    .card-footer { border-top-color: $LIGHT-BORDER; }
    
    .metrica {
        background-color: $WHITE;
        border-color: $LIGHT-BORDER;
        .count { color: $DARK-TEXT; }
    }
    
    &:hover { box-shadow: 0 8px 20px rgba(0,0,0,0.1); }
}

.theme-dark {
    background-color: $SUBTLE-BG-DARK;
    .proyecto-tarjeta {
            background-color: $SUBTLE-BG-DARK;

    }
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    border-color: rgba($WHITE, 0.05);
    
    .proyecto-titulo { color: $LIGHT-TEXT; }
    .proyecto-descripcion { color: $GRAY-COLD; }
    .card-footer { border-top-color: rgba($WHITE, 0.1); }
    
    .metrica {
        background-color: $BLUE-MIDNIGHT;
        border-color: rgba($WHITE, 0.05);
        .count { color: $LIGHT-TEXT; }
    }
    
    // 2. CORREGIDO AQUÍ: Se eliminó el código duplicado y se usa color.adjust correctamente
    &:hover { 
        box-shadow: 0 8px 25px rgba(0,0,0,0.5);  
        background-color: color.adjust($SUBTLE-BG-DARK, $lightness: 5%); 
    }
}
</style>