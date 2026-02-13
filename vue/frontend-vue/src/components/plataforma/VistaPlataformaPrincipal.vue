<template>
  <div class="plataforma-layout" :class="{ 'theme-dark': isDark, 'theme-light': !isDark }">
    
    <BarraLateralPlataforma :is-open="isSidebarOpen" />
    
    <div class="plataforma-contenido" :class="{ 'shifted': isSidebarOpen }">
      
      <EncabezadoPlataforma @toggle-sidebar="toggleSidebar" :is-sidebar-open="isSidebarOpen" />
      
      <div class="dashboard-grid">
    <TarjetasPlataforma class="grid-item-cards" />
    
    <div class="grid-item-summaries"> 
        <EstadoSistema :is-dark="isDark" /> 
        <ResumenAnalisisEnergetico :is-dark="isDark" /> </div>
    
    <ActividadReciente class="grid-item-activity" :is-dark="isDark" /> 
</div>

    </div>
  </div>
</template>

<script>
import BarraLateralPlataforma from './BarraLateralPlataforma.vue';
import EncabezadoPlataforma from './EncabezadoPlataforma.vue';
import TarjetasPlataforma from './TarjetasPlataforma.vue';
import EstadoSistema from './EstadoSistema.vue'; 
import ActividadReciente from './ActividadReciente.vue';

export default {
  name: 'VistaPlataformaPrincipal',
  components: {
    BarraLateralPlataforma,
    EncabezadoPlataforma,
    TarjetasPlataforma,
    EstadoSistema, 
    ActividadReciente, 
  },
  data() {
    return {
      isDark: false, 
      isSidebarOpen: true, 
    };
  },
  mounted() {
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
    toggleSidebar() {
      this.isSidebarOpen = !this.isSidebarOpen;
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
// LAYOUT PRINCIPAL
// ----------------------------------------
.plataforma-layout {
  display: flex;
  width: 100%;
  min-height: 100vh;
  transition: background-color 0.3s;
  background-color: $WHITE-SOFT; 
}


// ----------------------------------------
// DASHBOARD GRID (Distribución de Tarjetas y Módulos)
// ----------------------------------------

.dashboard-grid {
    // ...
    // Habilitar la rejilla de 2 columnas para los módulos inferiores
    display: grid; 
    
    grid-template-columns: 2fr 3fr; /* Divide el espacio restante en 5 partes, 2 para la izquierda, 3 para la derecha */
    
    gap: 20px; 
    padding: 0 40px 40px 40px; 
}
.grid-item-cards {
    /* La fila de las 4 tarjetas debe ocupar las 5 partes del ancho */
    grid-column: 1 / span 2; 
}

.grid-item-metrics {
    /* Estado del Sistema (ocupa 2/5 del ancho total) */
    grid-column: 1 / 2;
}

.grid-item-activity {
    /* Actividad Reciente (ocupa 3/5 del ancho total) */
    grid-column: 2 / 3;
}


// ----------------------------------------
// ESTILOS DE MÓDULOS INFERIORES (TEMPORAL)
// ----------------------------------------
.modulo-estado {
    background-color: $BLUE-MIDNIGHT; 
    color: $LIGHT-TEXT; // 👈 Ahora usa la variable definida arriba
    padding: 25px;
    height: 300px;
    border-radius: 15px;
    box-shadow: 0 8px 15px rgba(0, 0, 0, 0.5);
}

.modulo-actividad {
    background-color: #fff;
    color: $DARK-TEXT;
    padding: 25px;
    height: 300px;
    border-radius: 15px;
    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.05);
}


// ----------------------------------------
// TEMAS (Para el fondo de la página)
// ----------------------------------------

.theme-light {
  background-color: $WHITE-SOFT; 
  .plataforma-contenido {
    background-color: $WHITE-SOFT;
  }
}

.theme-dark {
  background-color: $DARK-BG-CONTRAST;
  .plataforma-contenido {
    background-color: $DARK-BG-CONTRAST;
  }
}


</style>