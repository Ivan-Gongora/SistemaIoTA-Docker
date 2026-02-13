<template>
    <div class="sensor-card" :class="{ 'theme-dark-card': isDark, 'disabled': !sensor.habilitado }">
        <div class="header-status">
            <div class="name-group">
                <i :class="getSensorIcon(sensor.tipo)" class="sensor-icono"></i>
                    <router-link :to="{ name: 'DetalleSensor', params: { id: sensor.id } }" class="sensor-card-link">

                <h3 class="sensor-nombre">{{ sensor.nombre }}</h3>
                </router-link>
            </div>
            
            <span class="status-badge" :class="sensor.habilitado ? 'active' : 'inactive'">
                {{ sensor.habilitado ? 'Activo' : 'Inactivo' }}
            </span>
        </div>

        <p class="sensor-type-description">
            Tipo: {{ sensor.tipo }} | Creado: {{ formatRelativeTime(sensor.fecha_creacion) }}
        </p>

        <div class="metricas-resumen">
            <div class="metrica-item">
                <i class="bi bi-rulers"></i>
                <span>Campos de Medición</span>
                <span class="count">{{ sensor.total_campos || 0 }}</span> 
            </div>
        </div>

        <div class="footer-actions">
            <template v-if="sensor.mi_rol === 'Propietario' || sensor.mi_rol === 'Colaborador'">
            <button @click.stop="openEditModal(sensor)" class="btn-action btn-edit" title="Modificar Sensor">
                <i class="bi bi-pencil"></i>
            </button>
            <button @click.stop="confirmarEliminacion(sensor.id, sensor.nombre)" class="btn-action btn-delete" title="Eliminar Sensor">
                <i class="bi bi-trash"></i>
            </button>
            </template>
        </div>
    </div>
    
</template>

<script>
// TarjetaSensor.vue <script>

export default {
    name: 'TarjetaSensor',
    props: {
        sensor: {
            type: Object,
            required: true,
            default: () => ({ id: null, nombre: 'Sensor de prueba', tipo: 'General', habilitado: false, fecha_creacion: null, total_campos: 0 }) // 🚨 Añadido total_campos
        },
        isDark: {
            type: Boolean,
            required: true
        }
    },
    emits: ['edit-sensor', 'delete-sensor', 'view-fields'],
    
    methods: {
        // Mapeo de Iconos
        getSensorIcon(type) {
             const lowerType = (type || '').toLowerCase();
             if (lowerType.includes('temp') || lowerType.includes('hum')) return 'bi bi-thermometer-half';
             if (lowerType.includes('movimiento')) return 'bi bi-person-bounding-box';
             if (lowerType.includes('gas')) return 'bi bi-cloud-haze2-fill';
             return 'bi bi-cpu';
        },
        formatRelativeTime(isoString) {
             if (!isoString) return 'N/A';
             return isoString.substring(0, 10); 
        },
        // // Navegar a la vista de Campos del Sensor
        // viewFields(sensorId) {
        //      this.$router.push(`/detalle-sensor/${sensorId}`);
        // },
        openEditModal(sensor) {
            this.$emit('edit-sensor', sensor); // Emite el evento que el padre escucha
        },
        
        confirmarEliminacion(id, nombre) {
            this.$emit('delete-sensor', id, nombre); // Emite el evento que el padre escucha
        },
    }
}
</script>

<style scoped lang="scss">
// ----------------------------------------
// VARIABLES DE LA PALETA
// ----------------------------------------
// $PRIMARY-PURPLE: #8A2BE2;
// $SUCCESS-COLOR: #1ABC9C;
// $ERROR-COLOR: #E74C3C;
// $GRAY-COLD: #99A2AD;
// $DARK-TEXT: #333333;
// $LIGHT-TEXT: #E4E6EB;
// $SUBTLE-BG-DARK: #2B2B40; 
// $SUBTLE-BG-LIGHT: #FFFFFF;
// $BLUE-MIDNIGHT: #1A1A2E; 

// ----------------------------------------
// ESTILOS BASE DE LA TARJETA
// ----------------------------------------
.sensor-card {
    background-color: $SUBTLE-BG-LIGHT;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
    transition: all 0.3s ease;
    cursor: pointer; /* Indica que la tarjeta es navegable */
    
    &:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.15);
    }
    
    &.disabled {
        opacity: 0.7;
        filter: grayscale(10%);
        cursor: default;
    }
}

.header-status {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
}

.name-group {
    display: flex;
    align-items: center;
}

.sensor-icono {
    font-size: 1.5rem;
    color: $PRIMARY-PURPLE;
    margin-right: 15px;
}

.sensor-nombre {
    font-size: 1.15rem;
    font-weight: 600;
    margin: 0;
}

.status-badge {
    font-size: 0.75rem;
    padding: 3px 8px;
    border-radius: 4px;
    font-weight: 600;
    
    &.active {
        background-color: rgba($SUCCESS-COLOR, 0.2);
        color: $SUCCESS-COLOR;
    }
    &.inactive {
        background-color: rgba($ERROR-COLOR, 0.2);
        color: $ERROR-COLOR;
    }
}

.sensor-type-description {
    font-size: 0.85rem;
    color: $GRAY-COLD;
    margin-bottom: 15px;
}

// ----------------------------------------
// MÉTRICAS Y ACCIONES
// ----------------------------------------
.metricas-resumen {
    margin-bottom: 15px;
    padding: 10px 0;
    border-top: 1px solid rgba($GRAY-COLD, 0.2);
    
    .metrica-item {
        display: flex;
        align-items: center;
        gap: 10px;
        
        i { color: $PRIMARY-PURPLE; font-size: 1rem; }
        span { font-size: 0.9rem; }
        .count { font-weight: 700; color: $PRIMARY-PURPLE; margin-left: auto; }
    }
}

.footer-actions {
    display: flex;
    justify-content: flex-end;
    gap: 10px;
    
    .btn-action {
        background: none;
        border: none;
        color: $GRAY-COLD;
        font-size: 1.1rem;
        cursor: pointer;
        transition: color 0.2s;
        
        &:hover { color: $PRIMARY-PURPLE; }
        &.btn-delete:hover { color: $ERROR-COLOR; }
    }
}

// ----------------------------------------
// TEMAS
// ----------------------------------------

// MODO CLARO (Define los colores del valor para cada métrica)
.theme-light-card {
    color: $DARK-TEXT;
     // 🚨 AÑADIR EL FONDO CLARO AQUÍ:
    background: linear-gradient(135deg, $SUBTLE-BG-LIGHT 70%, #f0f8ff 100%);
    color: $DARK-TEXT;
    // Asignar colores a los valores por defecto (se hará en DetalleProyecto.vue)
    .value { color: $SUCCESS-COLOR; } /* Verde para conteos */
}

// MODO OSCURO (Contraste fuerte)
.theme-dark-card {
    background-color: $BLUE-MIDNIGHT;
    color: $LIGHT-TEXT;
    box-shadow: 0 6px 15px rgba(0, 0, 0, 0.4);
    
    .title, .placeholder-note { color: $GRAY-COLD; }
    
    // Aseguramos que el valor grande sea blanco brillante
    .value { 
        color: $LIGHT-TEXT; 
    } 
}
</style>