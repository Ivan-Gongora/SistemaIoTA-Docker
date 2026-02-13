import pymysql
import time

# -----------------------------------------------------------
# CONFIGURACIÓN DE LA BASE DE DATOS
# -----------------------------------------------------------
# Asegúrate de que coincida con tu base de datos en XAMPP
DB_CONFIG = {
    'host': 'localhost',
    'user': 'sistemaiot',      # El usuario que creaste en tu SQL
    'password': 'raspberry',  # La contraseña que definiste
    'database': 'sistemaiotA_db', # El nombre de tu base de datos
    'port': 3306
}

def conectar_db():
    """Establece conexión con la base de datos MySQL."""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        print("Conexión a MySQL (XAMPP) exitosa.")
        return conn
    except pymysql.Error as e:
        print(f"Error al conectar a MySQL: {e}")
        return None

def ejecutar_agregacion(conn):
    """
    Lee la tabla 'valores', calcula los agregados por hora
    y los inserta en 'valores_agregados'.
    """
    
    # Esta consulta SQL hace todo el trabajo pesado:
    # 1. Selecciona los datos de 'valores'.
    # 2. Agrupa por campo_id, fecha y hora.
    # 3. Calcula MIN, MAX, AVG, y COUNT.
    # 4. Inserta los resultados en 'valores_agregados'.
    # 5. ON DUPLICATE KEY UPDATE: Si el script se ejecuta de nuevo,
    #    actualiza los registros en lugar de fallar.
    
    # 
    sql_aggregate = """
    INSERT INTO valores_agregados 
        (campo_id, fecha, hora, valor_min, valor_max, valor_avg, valor_sum, total_registros)
    SELECT
        v.campo_id,
        DATE(v.fecha_hora_lectura) AS fecha,
        HOUR(v.fecha_hora_lectura) AS hora,
        
        -- Min y Max se calculan para todos
        MIN(v.valor) AS valor_min,
        MAX(v.valor) AS valor_max,
        
        -- 🚨 Lógica Condicional:
        -- Si el nombre es 'Movimiento', AVG es NULL.
        CASE 
            WHEN cs.nombre = 'Movimiento' THEN NULL
            ELSE AVG(v.valor)
        END AS valor_avg,
        
        -- Si el nombre es 'Movimiento', calculamos SUM().
        CASE
            WHEN cs.nombre = 'Movimiento' THEN SUM(v.valor)
            ELSE NULL
        END AS valor_sum,
        
        COUNT(*) AS total_registros
    FROM
        valores v
    JOIN 
        campos_sensores cs ON v.campo_id = cs.id 
    GROUP BY
        v.campo_id, cs.nombre, fecha, hora 
    
    -- Actualizamos los campos correspondientes
    ON DUPLICATE KEY UPDATE
        valor_min = VALUES(valor_min),
        valor_max = VALUES(valor_max),
        valor_avg = VALUES(valor_avg),       
        valor_sum = VALUES(valor_sum),       
        total_registros = VALUES(total_registros);
    """
    
    try:
        with conn.cursor() as cursor:
            print("Vaciando resúmenes anteriores (TRUNCATE)...")
            cursor.execute("TRUNCATE TABLE valores_agregados;") 
            
            print("Ejecutando agregación inteligente (AVG/SUM)...")
            start_time = time.time()
            
            affected_rows = cursor.execute(sql_aggregate)
            
            conn.commit()
            end_time = time.time()
            
            print("\n" + "="*30)
            print("Agregación completada.")
            print(f"Tiempo de procesamiento de agregados: {end_time - start_time:.2f} segundos.")
            print(f"Total de registros de resumen (por hora) generados: {affected_rows}")
            
    except pymysql.Error as e:
        print(f"Error durante la agregación SQL: {e}")
        conn.rollback()

def main():
    conn = conectar_db()
    if conn:
        try:
            ejecutar_agregacion(conn)
        finally:
            conn.close()
            print("Conexión a MySQL cerrada.")

# --- Ejecutar el script ---
if __name__ == "__main__":
    main()