<template>
  <div class="encabezado-plataforma" :class="{ 'theme-dark': isDark, 'theme-light': !isDark }">
    
    <div class="header-content">
      <div class="titulo-area">
        
        <button @click="emitToggle" class="btn-toggle" title="Ocultar/Mostrar Barra Lateral">
<i :class="isSidebarOpen ? 'bi bi-arrow-left-circle-fill' : 'bi bi-list'"></i>

</button>
        
        <div class="title-text-group"> 
            <h1 class="titulo-principal mb-1">{{ titulo }}</h1>
            <p v-if="subtitulo" class="subtitulo">{{ subtitulo }}</p>
        </div>
      </div>
      
      <div class="status-area">
        <button class="btn-status">
          <i class="fas fa-circle status-dot"></i> 
          Sistema Operativo
        </button>
      </div>
    </div>
    <hr class="header-divider" :class="{ 'dark-divider': isDark }">
  </div>
</template>

<script>
export default {
  name: 'EncabezadoPlataforma',
  props: {
    titulo: {
      type: String,
      default: 'Panel de Control'
    },
    subtitulo: {
      type: String,
      default: 'Monitoreo en tiempo real de tu infraestructura IoT'
    },
     // 🚨 NUEVA PROP: Recibe el estado del Layout
    isSidebarOpen: { 
        type: Boolean,
        default: true,
    }
  },
  data() {
    return {
      isDark: false, // Estado para la detección de modo oscuro
    };
  },
  mounted() {
    // 1. Inicializar la detección de tema
    this.detectarTemaSistema();
    
    // 2. Añadir listener para cambios de tema
    if (window.matchMedia) {
      window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', this.handleThemeChange);
    }
  },
   beforeUnmount() { // 👈 CORRECCIÓN A beforeUnmount
    // Limpiar el listener al destruir el componente
    if (window.matchMedia) {
      window.matchMedia('(prefers-color-scheme: dark)').removeEventListener('change', this.handleThemeChange);
    }
  },
  methods: {
     emitToggle() {
        this.$emit('toggle-sidebar'); 
    },
    handleThemeChange(event) {
      this.isDark = event.matches;
    },
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
// ----------------------------------------
// VARIABLES DE LA PALETA "IoT SPECTRUM"
// ----------------------------------------
// $PRIMARY-PURPLE: #8A2BE2; // Azul Violeta
// $SUCCESS-COLOR: #1ABC9C;  // Verde Menta (para el botón de status)
// $GRADIENT-SUCCESS: linear-gradient(to right, #00C853, #1ABC9C); // Gradiente del botón
// $WHITE-SOFT: #F7F9FC;     // Fondo Claro
// $BLUE-MIDNIGHT: #1A1A2E;  // Fondo Oscuro
// $DARK-TEXT: #333333;      // Texto Claro (Modo Light)
// $LIGHT-TEXT: #E4E6EB;     // Texto Oscuro (Modo Dark)
// $GRAY-COLD: #99A2AD;      // Subtítulos
// $HEADER-BG-DARK: #2B2B40; // Fondo de encabezado en modo oscuro

// ----------------------------------------
// ESTRUCTURA BASE
// ----------------------------------------
.encabezado-plataforma {
  width: 100%;
  padding: 20px 40px 10px 40px; /* Más padding para que respire */
  margin-bottom: 20px;
  box-sizing: border-box;
  transition: background-color 0.3s, color 0.3s;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: relative; // 🚨 Añadir para poder posicionar hijos con absolute si es necesario
}


.titulo-area {
    display: flex; /* 🚨 CRÍTICO: Debe ser flex para alinear el botón */
    align-items: center; /* Alinea botón y texto verticalmente */
    /* ELIMINA: flex-direction: column; si todavía existe en tu código */
}
// 🚨 NUEVO: Grupo para título y subtítulo para apilarlos
// Aseguramos que el título y subtítulo se apilen correctamente
.title-text-group {
    display: flex;
    flex-direction: column; /* Apila el título y subtítulo */
    align-items: flex-start;
}

.icon-title {
    font-size: 1.5rem;
    margin-right: 10px;
    color: $PRIMARY-PURPLE;
  }
// 🚨 NUEVO ESTILO: Contenedor para el botón y el título
.title-row {
    display: flex; /* Habilita Flexbox */
    align-items: center; /* Alinea botón y título al centro vertical */
    margin-bottom: 5px;
}


.titulo-principal {
    font-size: 1.75rem;
    font-weight: 600;
    margin-bottom: 0 !important; /* Fuerza la eliminación de margen inferior */
    line-height: 1.2; // Mejorar la alineación del texto
}

.subtitulo {
    font-size: 0.9rem;
    margin-top: 5px; 
    opacity: 0.9;
}
// 🚨 ESTILOS DEL BOTÓN DE TOGGLE (Haciéndolo MUY visible)
// EncabezadoPlataforma.vue <style>
// ... (Variables de color deben estar definidas antes)

// 🚨 ESTILOS DEL BOTÓN DE TOGGLE (CORREGIDOS)
.btn-toggle {
    background: none; 
    border: none;
    cursor: pointer;
    font-size: 1.8rem;
    margin-right: 20px;
    padding: 5px; 
    min-width: 40px; 
    min-height: 40px; 
    display: flex; 
    justify-content: center;
    align-items: center;
    transition: color 0.3s, transform 0.2s ease-in-out;
    outline: none;

    // 🚨 1. Asignar el color base del botón directamente (ya resuelve la visibilidad del ícono)
    .theme-light & { 
        color: #555; 
    }
    .theme-dark & { 
        color: $LIGHT-TEXT; 
    } 

    // 🚨 2. Estilos para el ÍCONO (i) (Solo transiciones, hereda el color del botón)
    i {
        transition: transform 0.2s;
        display: block; // Asegurar que el ícono es un bloque dentro del flex
    }

    // Estilo al pasar el mouse
    &:hover {
        color: $PRIMARY-PURPLE; /* Cambia el color del botón (y el ícono hereda) */
        
        i {
            transform: scale(1.1); /* Aplica el efecto solo al ícono */
        }
    }

    &:active {
        transform: scale(0.95);
    }
}

// ... (resto de estilos)

.header-divider {
  border: none;
  height: 1px;
  background-color: rgba($GRAY-COLD, 0.2);
  margin: 15px 0 0 0;
}

// ----------------------------------------
// TEMAS Y COLORES
// ----------------------------------------

// MODO CLARO
.theme-light {
  background-color: $WHITE-SOFT;
  color: $DARK-TEXT;
  border-bottom: 1px solid #eee;

  .titulo-principal {
    color: $DARK-TEXT; /* Título oscuro */
  }
  .subtitulo {
    color: $GRAY-COLD; /* Subtítulo más sutil */
  }
  .header-divider {
    background-color: #eee;
  }
}

// MODO OSCURO
.theme-dark {
  background-color: $HEADER-BG-DARK; /* Un tono más claro que el sidebar */
  color: $LIGHT-TEXT;
  border-bottom: 1px solid #3e3e4f;
  
  .titulo-principal {
    color: $LIGHT-TEXT;
  }
  .subtitulo {
    color: rgba($LIGHT-TEXT, 0.7);
  }
  .header-divider {
    background-color: #3e3e4f;
  }
  .icon-title {
    color: $PRIMARY-PURPLE;
  }
}


// ----------------------------------------
// ESTILOS DEL BOTÓN DE STATUS
// ----------------------------------------

.btn-status {
  background: $GRADIENT-SUCCESS;
  color: #fff;
  border: none;
  padding: 8px 15px;
  border-radius: 20px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: default; /* No es un botón interactivo */
  box-shadow: 0 4px 10px rgba($SUCCESS-COLOR, 0.4);
  transition: transform 0.2s;

  &:hover {
    transform: translateY(-1px);
    box-shadow: 0 6px 15px rgba($SUCCESS-COLOR, 0.6);
  }

  .status-dot {
    font-size: 0.7rem;
    margin-right: 5px;
  }
}
</style>