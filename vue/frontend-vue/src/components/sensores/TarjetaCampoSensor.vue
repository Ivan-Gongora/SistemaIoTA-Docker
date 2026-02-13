<template>
  <div class="campo-card" :class="{ 'theme-dark': isDark, 'theme-light': !isDark }">
    
    <div class="card-header">
      <i :class="getIcon(campo.magnitud_tipo)" class="campo-icono"></i>
      <h4 class="campo-nombre">{{ campo.nombre }}</h4>
    </div>

    <div class="valor-principal">
      {{ campo.ultimo_valor ?? 'N/A' }}
      <span class="simbolo">{{ campo.simbolo_unidad }}</span>
    </div>

    <div class="card-footer">
      <span class="tipo-dato-badge">Tipo: {{ campo.tipo_valor }}</span>

      <!-- Permiso según rol -->
      <div class="acciones" v-if="usuarioPuedeEditar">
        <button @click.stop="$emit('edit-campo', campo)" class="btn-action" title="Modificar">
          <i class="bi bi-pencil"></i>
        </button>

        <button @click.stop="$emit('delete-campo', campo.id, campo.nombre)" class="btn-action btn-delete" title="Eliminar">
          <i class="bi bi-trash"></i>
        </button>
      </div>

    </div>

  </div>
</template>

<script>
export default {
  name: 'TarjetaCampoSensor',

  props: {
    campo: {
      type: Object,
      required: true,
      default: () => ({
        id: null,
        nombre: 'Cargando...',
        tipo_valor: 'N/A',
        ultimo_valor: 'N/A',
        simbolo_unidad: '',
        magnitud_tipo: ''
      })
    },

    // TEMA
    isDark: {
      type: Boolean,
      required: true
    },

    // 🔥 NUEVO: EL ROL DEL USUARIO (PROPIETARIO / COLABORADOR / INVITADO)
    rol: {
      type: String,
      required: true,
      default: "INVITADO"
    }
  },

  emits: ['edit-campo', 'delete-campo'],

  computed: {
    usuarioPuedeEditar() {
      // 🔥 Los roles ahora vienen en MAYÚSCULAS desde el backend
      return this.rol === "PROPIETARIO" || this.rol === "COLABORADOR" || this.rol === 'Colaborador' || this.rol === 'Propietario';
    }
  },

  methods: {
    getIcon(magnitud) {
      if (!magnitud) return 'bi bi-question-lg';
      const lowerMag = magnitud.toLowerCase();

      if (lowerMag.includes('temperatura')) return 'bi bi-thermometer-half';
      if (lowerMag.includes('humedad')) return 'bi bi-droplet-half';
      if (lowerMag.includes('electricidad')) return 'bi bi-lightning-charge-fill';

      if (lowerMag.includes('energía')) return 'bi bi-battery-charging';
      if (lowerMag.includes('potencia')) return 'bi bi-lightning';
      if (lowerMag.includes('iluminación') || lowerMag.includes('luz')) return 'bi bi-sun';
      if (lowerMag.includes('presión')) return 'bi bi-gauge';
      if (lowerMag.includes('distancia') || lowerMag.includes('longitud')) return 'bi bi-rulers';
      if (lowerMag.includes('masa') || lowerMag.includes('peso')) return 'bi bi-box-seam';
      if (lowerMag.includes('volumen')) return 'bi bi-box';
      if (lowerMag.includes('flujo')) return 'bi bi-arrow-repeat';
      if (lowerMag.includes('frecuencia')) return 'bi bi-activity';
      if (lowerMag.includes('ángulo')) return 'bi bi-arrow-counterclockwise';

      if (lowerMag.includes('estado')) return 'bi bi-toggle-on';
      if (lowerMag.includes('tiempo') || lowerMag.includes('segundo')) return 'bi bi-clock';

      if (lowerMag.includes('concentración') || lowerMag.includes('ppm')) return 'bi bi-flask';
      if (lowerMag.includes('sonido') || lowerMag.includes('ruido')) return 'bi bi-volume-up';

      if (lowerMag.includes('conteo')) return 'bi bi-hash';

      return 'bi bi-speedometer2';
    }
  }
};
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
// ESTILOS DE LA TARJETA
// ----------------------------------------
.campo-card {
    background-color: $SUBTLE-BG-LIGHT;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
    transition: all 0.3s ease;
    border: 1px solid #eee;
    
    &:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.15);
    }
}

.card-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 15px;
    
    .campo-icono {
        font-size: 1.5rem;
        color: $PRIMARY-PURPLE;
    }
    .campo-nombre {
        font-size: 1.1rem;
        font-weight: 600;
        margin: 0;
    }
}

.valor-principal {
    font-size: 2.2rem;
    font-weight: 700;
    text-align: center;
    margin-bottom: 15px;
    
    .simbolo {
        font-size: 1.2rem;
        font-weight: 500;
        color: $GRAY-COLD;
        margin-left: 5px;
    }
}

.card-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-top: 10px;
    border-top: 1px solid rgba($GRAY-COLD, 0.2);
    
    .tipo-dato-badge {
        font-size: 0.75rem;
        padding: 3px 8px;
        border-radius: 4px;
        background-color: rgba($GRAY-COLD, 0.2);
        color: $GRAY-COLD;
        font-weight: 600;
    }
    
    .acciones {
        display: flex;
        gap: 10px;
    }
    .btn-action {
        background: none; border: none;
        color: $GRAY-COLD;
        font-size: 1rem;
        cursor: pointer;
        padding: 5px;
        &:hover { color: $PRIMARY-PURPLE; }
        &.btn-delete:hover { color: #E74C3C; }
    }
}

// ----------------------------------------
// TEMAS
// ----------------------------------------
.theme-dark {
    background-color: $SUBTLE-BG-DARK;
    color: $LIGHT-TEXT;
    box-shadow: 0 6px 15px rgba(0, 0, 0, 0.4);
    border-color: rgba($LIGHT-TEXT, 0.1);
    
    .campo-icono { color: $LIGHT-TEXT; }
    .valor-principal .simbolo { color: $GRAY-COLD; }
    .card-footer { border-top-color: rgba($LIGHT-TEXT, 0.1); }
    .tipo-dato-badge {
        background-color: rgba($GRAY-COLD, 0.3);
        color: $LIGHT-TEXT;
    }
}
</style>