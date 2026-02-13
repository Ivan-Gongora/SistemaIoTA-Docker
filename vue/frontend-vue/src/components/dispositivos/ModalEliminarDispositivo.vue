<template>
  <div class="modal-base" @click.self="$emit('cancelar')">
    <div class="modal-contenido-confirmacion" :class="{ 'theme-dark': isDark, 'theme-light': !isDark }">
      
      <div class="modal-header">
        <h2 class="text-danger">Confirmar Eliminación</h2>
        <button @click="$emit('cancelar')" class="btn-cerrar">&times;</button>
      </div>
      
      <div class="modal-body">
        <p class="warning-text">
          <i class="bi bi-exclamation-triangle-fill icon-warning"></i>
          ¿Estás seguro de que deseas eliminar el dispositivo <strong>{{ dispositivoNombre }}</strong>? Esta acción no tiene modo de revertirse.
        </p>
        
        <p class="small-info">ID Dispositivo: {{ dispositivoId }}</p>
        <p class="small-info">Se eliminarán todos sus sensores, campos y datos asociados.</p>
      </div>
      
      <div class="pie-modal">
        <button class="btn-cancelar-accion" @click="$emit('cancelar')">Cancelar</button>
        <button 
            class="btn-confirmar-accion" 
            @click="$emit('confirmar', dispositivoId, proyectoId)"
        >
            Sí, Eliminar
        </button>
      </div>
    </div>
  </div>
</template>

<script>
// Usaremos este para obtener el ID del usuario logueado en el componente padre
// const API_BASE_URL = 'http://127.0.0.1:8001'; 

export default {
  name: 'ModalEliminarDispositivo',
  props: {
    dispositivoId: {
      type: [Number, String],
      required: true
    },
    dispositivoNombre: {
      type: String,
      required: true
    },
    proyectoId: { // Necesario para la URL de la API DELETE
        type: [Number, String],
        required: true
    }
  },
  data() {
    return {
      isDark: false,
    };
  },
  mounted() {
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      this.isDark = true;
    }
  },
};
</script>
<style scoped lang="scss">
@use 'sass:color'; // 🚨 CRÍTICO: Importar el módulo de color para usar color.adjust()

// // ----------------------------------------
// // VARIABLES DE LA PALETA
// // ----------------------------------------
// $PRIMARY-PURPLE: #8A2BE2; 
// $ERROR-COLOR: #FF5733; 
// $WHITE-SOFT: #F7F9FC;
// $BLUE-MIDNIGHT: #1A1A2E;
// $DARK-TEXT: #333333;
// $LIGHT-TEXT: #E4E6EB;
// $SUBTLE-BG-DARK: #2B2B40;
// $SUBTLE-BG-LIGHT: #FFFFFF;
// $GRAY-COLD: #99A2AD;


// ----------------------------------------
// BASE DEL MODAL (POSICIONAMIENTO)
// ----------------------------------------
.modal-base {
 position: fixed; top: 0; left: 0; width: 100%; height: 100%;
 background-color: rgba(0, 0, 0, 0.7);
 display: flex; justify-content: center; align-items: center;
 z-index: 9999;
}

.modal-contenido-confirmacion {
 width: 90%; max-width: 400px;
 border-radius: 15px; padding: 25px;
 box-shadow: 0 10px 30px rgba(0, 0, 0, 0.8);
 transition: background-color 0.3s, color 0.3s;
}

.modal-header {
 display: flex; justify-content: space-between; align-items: center;
 margin-bottom: 20px;
 h2 { font-size: 1.4rem; font-weight: 600; }
}
.btn-cerrar {
background: none; border: none; font-size: 1.8rem; cursor: pointer; opacity: 0.7;
 &:hover { opacity: 1; }
}

.modal-body {
 padding: 10px 0;
}

.warning-text {
 font-size: 1rem;
line-height: 1.4;
 font-weight: 500;
 .icon-warning {
 color: $ERROR-COLOR;
 margin-right: 8px;
 font-size: 1.1rem;
 }
}

.small-info {
 font-size: 0.85rem;
 margin-top: 10px;
 opacity: 0.7;
}

// ----------------------------------------
// PIE DE MODAL Y BOTONES DE ACCIÓN
// ----------------------------------------
.pie-modal {
 display: flex;
 justify-content: flex-end;
 gap: 10px;
 margin-top: 25px;
}

.btn-cancelar-accion {
 background-color: $GRAY-COLD;
 color: #fff;
 border: none;
 padding: 10px 15px;
 border-radius: 8px;
 cursor: pointer;
 transition: opacity 0.2s;
 &:hover { opacity: 0.8; }
}

.btn-confirmar-accion {
 background-color: $ERROR-COLOR;
 color:$WHITE;
 border: none;
 padding: 10px 15px;
 border-radius: 8px;
 cursor: pointer;
 transition: background-color 0.2s;
 &:hover { 
    background-color: color.adjust($DANGER-COLOR, $lightness: -10%);
 }
}


// ----------------------------------------
// TEMAS (DARK/LIGHT)
// ----------------------------------------
.theme-light .modal-contenido-confirmacion {
background-color: $SUBTLE-BG-LIGHT;
 color: $DARK-TEXT;
 .btn-cerrar { color: $DARK-TEXT; }
}

.theme-dark .modal-contenido-confirmacion {
 background-color: $SUBTLE-BG-DARK;
 color: $LIGHT-TEXT;
 .btn-cerrar { color: $LIGHT-TEXT; }
 .warning-text { color: $LIGHT-TEXT; }
 .btn-cancelar-accion { background-color: #444; }
}
</style>