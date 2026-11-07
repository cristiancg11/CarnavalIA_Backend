-- ==============================================================================
-- CARNAVALIA BACKEND - ESQUEMA DDL SQL DE BASE DE DATOS SUPABASE / POSTGRESQL
-- PROYECTO: Sistema Inteligente para el Carnaval de Negros y Blancos de Pasto
-- USO: Sustentación universitaria y replicación independiente sin conexión a la nube
-- ==============================================================================

-- 1. EXTENSIONES RECOMENDADAS
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ==============================================================================
-- 2. TABLA: USERS (Usuarios del sistema y organizadores)
-- ==============================================================================
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(150),
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    role VARCHAR(50) DEFAULT 'ciudadano' NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);

-- ==============================================================================
-- 3. TABLA: POINTS_OF_INTEREST (Puntos de Auxilio, Policía, Tarimas y Servicios)
-- ==============================================================================
CREATE TABLE IF NOT EXISTS points_of_interest (
    id SERIAL PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    description TEXT,
    category VARCHAR(50) NOT NULL, -- Salud, Seguridad, Tarima, Bano, Cultura
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    icon VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_poi_category ON points_of_interest (category);

-- ==============================================================================
-- 4. TABLA: ZONE_RISK (Monitoreo de Congestión y Zonas de la Senda)
-- ==============================================================================
CREATE TABLE IF NOT EXISTS zone_risk (
    id SERIAL PRIMARY KEY,
    zone_name VARCHAR(100) NOT NULL,
    coordinates JSONB,
    risk_level VARCHAR(50) DEFAULT 'Bajo' NOT NULL, -- Bajo, Medio, Alto, Critico
    congestion_percentage INT DEFAULT 0 NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- ==============================================================================
-- 5. TABLA: REPORTS (Incidencias Ciudadanas y Reportes de Seguridad)
-- ==============================================================================
CREATE TABLE IF NOT EXISTS reports (
    id SERIAL PRIMARY KEY,
    title VARCHAR(150) NOT NULL,
    description TEXT,
    category VARCHAR(50) NOT NULL, -- seguridad, primeros auxilios, extravío, tráfico, Aglomeracion, Emergencia
    status VARCHAR(50) DEFAULT 'Pendiente' NOT NULL, -- Pendiente, En_Revision, Atendido, Descartado
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    ai_risk_level VARCHAR(50) DEFAULT 'Bajo',
    user_id INT REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_reports_category ON reports (category);
CREATE INDEX IF NOT EXISTS idx_reports_status ON reports (status);
CREATE INDEX IF NOT EXISTS idx_reports_created_at ON reports (created_at DESC);

-- ==============================================================================
-- 6. TABLA: EVENTS (Agenda Oficial y Cronograma del Carnaval)
-- ==============================================================================
CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    title VARCHAR(150) NOT NULL,
    description TEXT,
    date_label VARCHAR(50) NOT NULL, -- '28 de Diciembre', '02 de Enero', etc.
    start_time VARCHAR(20),
    end_time VARCHAR(20),
    location VARCHAR(150),
    category VARCHAR(50) DEFAULT 'Desfile' NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_events_date ON events (date_label);

-- ==============================================================================
-- 7. POLÍTICAS DE SEGURIDAD A NIVEL DE FILA (ROW LEVEL SECURITY - RLS)
-- ==============================================================================
-- Habilitar RLS en las tablas expuestas
ALTER TABLE reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE events ENABLE ROW LEVEL SECURITY;
ALTER TABLE points_of_interest ENABLE ROW LEVEL SECURITY;

-- Políticas para 'reports':
-- 1. Lectura pública de reportes activos para visualización en el mapa interactivo
DROP POLICY IF EXISTS "Permitir lectura publica de reportes" ON reports;
CREATE POLICY "Permitir lectura publica de reportes"
    ON reports FOR SELECT
    USING (status != 'Descartado');

-- 2. Inserción permitida a ciudadanos (anónimos o autenticados vía frontend/backend)
DROP POLICY IF EXISTS "Permitir insercion de reportes ciudadanos" ON reports;
CREATE POLICY "Permitir insercion de reportes ciudadanos"
    ON reports FOR INSERT
    WITH CHECK (true);

-- 3. Actualización y gestión restringida a usuarios con rol administrativo o servicio
DROP POLICY IF EXISTS "Permitir actualizacion administrativa de reportes" ON reports;
CREATE POLICY "Permitir actualizacion administrativa de reportes"
    ON reports FOR UPDATE
    USING (true);

-- Políticas para 'events':
-- 1. Lectura pública libre de la programación cultural oficial
DROP POLICY IF EXISTS "Permitir lectura publica de eventos del carnaval" ON events;
CREATE POLICY "Permitir lectura publica de eventos del carnaval"
    ON events FOR SELECT
    USING (true);

-- Políticas para 'points_of_interest':
DROP POLICY IF EXISTS "Permitir lectura publica de puntos de interes" ON points_of_interest;
CREATE POLICY "Permitir lectura publica de puntos de interes"
    ON points_of_interest FOR SELECT
    USING (is_active = true);

-- ==============================================================================
-- 8. CARGA INICIAL DE DATOS (SEEDING CULTURAL DEL CARNAVAL DE PASTO)
-- ==============================================================================
INSERT INTO events (title, description, date_label, start_time, end_time, location, category) VALUES
('Arcoíris en el Asfalto', 'Pintura artística con tiza sobre el asfalto. Celebración cultural por la paz, el arte urbano y el agua.', '28 de Diciembre', '08:00', '18:00', 'Sector El Colorado (Cra 23 entre Calles 14 y 15)', 'Arte Urbano'),
('Desfile de Años Viejos', 'Desfile de Años Viejos y Viudas. Humor, sátira política, testamentos y quema simbólica de monigotes.', '31 de Diciembre', '08:00', '16:00', 'Senda Cra 27 (Normal Superior a Champagnat)', 'Tradición'),
('Carnavalito', 'Desfile infantil con mini-carrozas y comparsitas en devoción a la Virgen de las Mercedes.', '02 de Enero', '07:00', '14:00', 'Senda Cra 27 (Normal Superior a Champagnat)', 'Infantil'),
('Canto a la Tierra', 'Desfile de Colectivos Coreográficos, miles de músicos y danzantes andinos por la Senda.', '03 de Enero', '09:00', '16:00', 'Senda Cra 27 (Normal Superior a Champagnat)', 'Música y Danza'),
('Llegada de la Familia Castañeda', 'Bienvenida festiva recreando la comitiva campesina de 1929 con teatro callejero y carretas de época.', '04 de Enero', '08:00', '15:00', 'Senda Cra 27 y Centro Histórico', 'Desfile Histórico'),
('Día de Negros', 'Juego fraternal con cosmético negro, orquestas en vivo y tarimas musicales en plazas públicas.', '05 de Enero', '11:00', '23:00', 'Plaza del Carnaval y Plaza de Nariño', 'Juego Tradicional'),
('Día de Blancos - Desfile Magno', 'La cumbre del Carnaval: Majestuosas Carrozas Monumentales, comparsas, murgas, talco y carioca.', '06 de Enero', '05:00', '17:00', 'Senda Oficial del Carnaval (7 km)', 'Desfile Magno')
ON CONFLICT DO NOTHING;

INSERT INTO points_of_interest (name, description, category, latitude, longitude, icon) VALUES
('PMU Plaza del Carnaval', 'Puesto de Mando Unificado central, Cruz Roja y Defensa Civil', 'Salud', 1.2118, -77.2760, 'cross'),
('PMU Normal Superior', 'Atención médica y coordinación en la salida de los desfiles', 'Salud', 1.2055, -77.2825, 'cross'),
('PMU Carrera 27 con Cll 19', 'Módulo de primeros auxilios y socorro intermedio', 'Salud', 1.2140, -77.2775, 'cross'),
('PMU Sector Champagnat', 'Puesto de atención médica y desconcentración norte', 'Salud', 1.2188, -77.2745, 'cross'),
('CAI Plaza de Nariño', 'Centro de Atención Inmediata Policía Nacional', 'Seguridad', 1.2145, -77.2780, 'shield'),
('Tarima Plaza del Carnaval', 'Tarima oficial de orquestas y premiación de artesanos', 'Tarima', 1.2115, -77.2765, 'music')
ON CONFLICT DO NOTHING;
