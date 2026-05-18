// src/stores/uploadStore.js
import { reactive } from 'vue';

// 1. Estado global (variables que sobreviven a los cambios de página)
export const uploadState = reactive({
  uploading: false,
  progress: 0,
  processedRows: 0,
  totalRows: 0,
  status: { message: '', type: '' },
  mostrarWidget: false // Controla si se ve la ventanita flotante
});

// 2. Funciones auxiliares de formato
const parseCSV = (text) => {
  const lines = text.split('\n').map(l => l.trim()).filter(l => l !== '');
  if (lines.length === 0) return [];
  const headers = lines[0].split(',').map(h => h.trim());
  return lines.slice(1).map(line => {
    const values = line.split(',');
    const entry = {};
    headers.forEach((header, index) => {
      entry[header] = values[index]?.trim();
    });
    return entry;
  });
};

const formatRowToJson = (row, proyectoId, dispositivoId) => {
  return {
    proyecto: proyectoId,
    dispositivo: dispositivoId,
    fecha: row.Fecha,
    hora: row.Hora,
    id_paquete: parseInt(row.Paquete_id) || 1,
    sensores: [
      { nombre: "DHT22", datos: { Temperatura: row.Temperatura, Humedad: row.Humedad } },
      { nombre: "SCT-013-000", datos: { Corriente: row.Corriente, Potencia: row.Potencia, Energia: row.Energia } },
      { nombre: "BH1750", datos: { Iluminacion: row.Iluminacion } },
      { nombre: "PIR HC-SR501", datos: { Movimiento: row.Movimiento } },
      { nombre: "Lógica de Control", datos: { "Estado Luz Ideal": row.Estado_Luz_Ideal, "Motivo Luz": row.Motivo_Luz, "Estado Clima Ideal": row.Estado_Clima_Ideal, "Motivo Clima": row.Motivo_Clima,"Temp_Ext": row.Temp_Ext, "Hum_Ext": row.Hum_Ext } }
    ]
  };
};

// 3. Lógica principal de subida (La que corre en segundo plano)
export const iniciarSubidaGlobal = async (file, proyectoId, dispositivoId) => {
  if (!file) return;
  
  uploadState.uploading = true;
  uploadState.mostrarWidget = true; // Activamos el widget para que se vea en toda la app
  uploadState.progress = 0;
  uploadState.processedRows = 0;
  uploadState.status = { message: 'Iniciando lectura de bitácora...', type: 'info' };

  const reader = new FileReader();
  reader.onload = async (e) => {
    try {
      const text = e.target.result;
      const rows = parseCSV(text);
      uploadState.totalRows = rows.length;
      
      if (uploadState.totalRows === 0) throw new Error("El archivo CSV está vacío.");

      const batchSize = 4000; // Usando el tamaño optimizado
      for (let i = 0; i < uploadState.totalRows; i += batchSize) {
        const batch = rows.slice(i, i + batchSize);
        const payloadBatch = batch.map(row => formatRowToJson(row, proyectoId, dispositivoId));

        const response = await fetch(`${window.API_BASE_URL || 'http://localhost:8000'}/api/guardar_lote_json/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payloadBatch)
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.message || 'Falla en el bloque de sincronización.');
        }

        uploadState.processedRows += batch.length;
        uploadState.progress = Math.round((uploadState.processedRows / uploadState.totalRows) * 100);
      }
      uploadState.status = { message: `Sincronización exitosa. ${uploadState.processedRows} registros guardados.`, type: 'success' };
    } catch (err) {
      uploadState.status = { message: `Fallo en el proceso: ${err.message}`, type: 'error' };
    } finally {
      uploadState.uploading = false;
      // Puedes poner un setTimeout aquí si quieres que el widget se cierre solo después de unos segundos
    }
  };
  reader.readAsText(file);
};