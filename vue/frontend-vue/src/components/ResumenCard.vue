<template>
  <div class="resumen-card" :class="{ 'theme-dark': isDark, 'theme-light': !isDark }">
    <div class="card-icon">
      <i :class="['bi', icono]"></i>
    </div>
    <div class="card-content">
      <h6 class="card-title">{{ titulo }}</h6>
      <p class="card-value">{{ valor }}</p>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ResumenCard',
  props: {
    titulo: String,
    valor: [String, Number],
    icono: String, // Clase de icono de Bootstrap, ej: "bi-lightning"
    isDark: {
      type: Boolean,
      default: false,
    },
  },
};
</script>

<style scoped lang="scss">
@use "sass:color";

$spacer: 1rem;
$border-radius: 12px;
$border-radius-sm: 8px;

.resumen-card {
  display: flex;
  align-items: center;
  // Reduce el gap en pantallas pequeñas
  gap: clamp(10px, 2vw, $spacer); 
  padding: clamp(12px, 2vw, $spacer); 
  border-radius: $border-radius;
  background-color: var(--card-bg);
  border: 1px solid var(--card-border);
  box-shadow: var(--shadow-color);
  transition: all 0.2s ease-in-out;
  height: 100%; 
  // Altura mínima fluida
  min-height: clamp(70px, 10vh, 90px); 

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
  }

  .card-icon {
    // Icono escala con la pantalla
    font-size: clamp(1.2rem, 3vw, 1.5rem); 
    color: $PRIMARY-PURPLE;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: clamp(6px, 1vw, 8px);
    background-color: rgba($PRIMARY-PURPLE, 0.15);
    border-radius: $border-radius-sm;
    // Ancho mínimo fluido para el contenedor del icono
    min-width: clamp(40px, 10vw, 50px); 
    height: clamp(40px, 10vw, 50px);
  }

  .card-content {
    flex-grow: 1;
    display: flex;
    flex-direction: column;
    justify-content: center;
    min-width: 0; // CRÍTICO: Permite que el texto se corte con ellipsis
  }

  .card-title {
    margin-bottom: 2px;
    font-size: clamp(0.75rem, 2vw, 0.85rem); 
    color: var(--text-color-secondary); 
    font-weight: 500;
    line-height: 1.2;
    // Manejo robusto de texto largo
    white-space: nowrap; 
    overflow: hidden;
    text-overflow: ellipsis; 
  }

  .card-value {
    // El valor se hace grande en escritorio y legible en móvil
    font-size: clamp(1.1rem, 4vw, 1.35rem); 
    font-weight: 700;
    color: var(--text-color-primary); 
    margin-bottom: 0;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    line-height: 1.1;
  }

  /* ------------------- TEMA OSCURO ------------------- */
  &.theme-dark {
    .card-title {
      color: color.adjust($LIGHT-TEXT, $alpha: -0.3); 
    }
    .card-value {
      color: $LIGHT-TEXT; 
    }
  }
}
</style>