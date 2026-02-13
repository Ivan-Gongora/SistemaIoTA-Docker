<template>
     <div 
        class="summary-card" 
        :class="{ 
            // 🚨 CORRECCIÓN: Usa la misma lógica de toggle que el layout maestro
            'theme-dark-card': isDark, 
            'theme-light-card': !isDark 
        }"
    >
        <div class="header-content">
            <div class="icon-box" :style="{ backgroundColor: card.color }">
                <i :class="card.icon"></i>
            </div>
            
            <div class="metrics-text">
                <p class="title">{{ card.title }}</p>
                <p class="value">{{ card.value }}</p>
            </div>
        </div>
        
        <p v-if="card.isPlaceholder" class="placeholder-note">
            *Funcionalidad futura
        </p>
    </div>
</template>

<script>
export default {
    name: 'TarjetaResumen',
    props: {
        // Objeto de la tarjeta (title, value, icon, color, isPlaceholder)
        card: {
            type: Object,
            // 🚨 Valor por defecto seguro para prevenir el error 'undefined'
            default: () => ({ 
                title: 'N/A', 
                value: 0, 
                icon: 'bi bi-info-circle', 
                color: '#999', 
                isPlaceholder: false 
            }),
        },
        // Propiedad heredada del padre para el tema
        isDark: {
            type: Boolean,
            required: true
        }
    }
}
</script>

<style scoped lang="scss">
// TarjetaResumen.vue <style>

// ----------------------------------------
// VARIABLES SCSS (Definidas en el componente)
// ----------------------------------------
// $PRIMARY-PURPLE: #8A2BE2;
// $SUCCESS-COLOR: #1ABC9C;
// $MAINTENANCE-COLOR: #FFC107;
// $ERROR-COLOR: #FF5733;
// $GRAY-COLD: #99A2AD;
// $LIGHT-TEXT: #E4E6EB;
// $DARK-TEXT: #333333;
// $SUBTLE-BG-LIGHT: #FFFFFF;
// $BLUE-MIDNIGHT: #1A1A2E; 

// ----------------------------------------
// ESTILOS DE LA TARJETA
// ----------------------------------------
.summary-card {
    // 🚨 QUITAR ESTILO POR DEFECTO: El fondo blanco sutil (linear-gradient)
    // debe estar SÓLO en .theme-light-card, no en el selector base.
    // background: linear-gradient(135deg, $SUBTLE-BG-LIGHT 70%, #f0f8ff 100%); <-- ELIMINAR O MOVER
    
    padding: 25px; 
    border-radius: 16px;
    height: 100%;
    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.05);
    transition: all 0.2s;
    cursor: default;
}

.header-content {
    display: flex;
    justify-content: space-between;
    align-items: flex-start; /* Alinea arriba */
    margin-bottom: 20px;
}

.icon-box {
    width: 35px; /* Más pequeño */
    height: 35px;
    border-radius: 8px;
    color: white;
    font-size: 1.1rem;
    // El color de fondo se define inline en el HTML para cada tarjeta
}

.metrics-text {
    .value {
        font-size: 2.5rem; /* Valor mucho más grande */
        font-weight: 700;
        margin-bottom: 5px;
        line-height: 1;
        transition: color 0.3s;
    }
    .title {
        font-size: 0.9rem;
        font-weight: 500;
        color: $GRAY-COLD; /* Título sutil */
    }
}

.placeholder-note {
    font-size: 0.75rem;
    font-style: italic;
    opacity: 0.7;
    margin-top: 10px;
    padding-top: 10px;
    border-top: 1px dashed;
}

// ----------------------------------------
// TEMAS Y ESQUEMAS DE COLOR (Adaptando el valor grande)
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