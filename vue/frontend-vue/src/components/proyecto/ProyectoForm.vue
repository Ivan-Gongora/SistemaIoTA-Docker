<template>
    <form @submit.prevent="submitForm">
        <div v-if="error" class="alert-error mb-3">{{ error }}</div>

        <div class="form-group mb-3">
            <label for="nombre">Nombre del Proyecto:</label>
            <input type="text" v-model="form.nombre" id="nombre" class="form-control" required />
        </div>
        
        <div class="form-group mb-3">
            <label for="tipo_industria">Tipo de Sector:</label>
            <select v-model="form.tipo_industria" id="tipo_industria" class="form-control" required>
                <option v-for="option in industryOptions" :key="option.value" :value="option.value">
                    {{ option.label }}
                </option>
            </select>
        </div>
        
        <div class="form-group mb-4">
            <label for="descripcion">Descripción:</label>
            <textarea v-model="form.descripcion" id="descripcion" class="form-control" rows="3" required></textarea>
        </div>
        
        <div class="d-flex justify-content-end">
            <button type="button" @click="$emit('cancel')" class="btn btn-secondary me-2">Cancelar</button>
            <button type="submit" class="btn btn-primary" :disabled="loading">
                <i v-if="loading" class="bi bi-arrow-clockwise fa-spin"></i>
                {{ loading ? 'Procesando...' : submitButtonText }}
            </button>
        </div>
    </form>
</template>
<script>
export default {
    name: 'ProyectoForm',
    props: {
        // Objeto de proyecto para EDICIÓN (contiene los datos actuales)
        initialData: {
            type: Object,
            // Proporcionamos un default con valores de cadena para evitar errores de null
            default: () => ({ 
                nombre: '', 
                descripcion: '', 
                tipo_industria: 'General' 
            })
        },
        submitButtonText: {
            type: String,
            default: 'Guardar'
        },
        loading: {
            type: Boolean,
            default: false
        },
        error: {
            type: String,
            default: null
        }
    },
    data() {
        return {
            // 🚨 CRÍTICO: Inicialización defensiva de form
            // Usamos '||' para garantizar que el valor de tipo_industria sea una cadena ('General') 
            // si initialData lo devuelve como null o undefined.
            form: {
                nombre: this.initialData.nombre || '',
                descripcion: this.initialData.descripcion || '',
                tipo_industria: this.initialData.tipo_industria || 'General', 
            },
            // Opciones para el dropdown de selección
            industryOptions: [
                { label: 'Hogar Inteligente', value: 'Hogar Inteligente' },
                { label: 'Agricultura de Precisión', value: 'Agricultura Precision' },
                { label: 'Monitoreo Ambiental', value: 'Monitoreo Ambiental' },
                { label: 'Industrial / Manufactura', value: 'Industrial' },
                { label: 'General / Otro', value: 'General' },
            ]
        };
    },
    watch: {
        // 🚨 CRÍTICO: Observar la data inicial para actualizar el formulario en modo Edición
        initialData: {
            handler(newData) {
                // Copia los nuevos datos y aplica la misma lógica defensiva para tipo_industria
                this.form = { 
                    ...newData,
                    tipo_industria: newData.tipo_industria || 'General' 
                };
            },
            // El deep: true asegura que el watcher detecte cambios dentro del objeto
            deep: true
        }
    },
    methods: {
        submitForm() {
            // Emite el evento 'submit' al componente padre (Modal) con la data del formulario
            // La data del formulario tiene el valor correcto, incluso si es 'General'.
            this.$emit('submit', this.form);
        }
    }
};
</script>
