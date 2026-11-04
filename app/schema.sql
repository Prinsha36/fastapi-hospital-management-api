CREATE TABLE IF NOT EXISTS departments(
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL , 
--  name VARCHAR(100) UNIQUE NOT NULL , #Department name cannot be duplicated
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP  
--     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP  #Record creation date and time

);

INSERT INTO departments (name, description) VALUES
('Cardiology', 'Department specializing in heart-related conditions.'),
('Neurology', 'Department focusing on disorders of the nervous system.'),
('Orthopedics', 'Department dealing with musculoskeletal issues.'),
('Pediatrics', 'Department providing medical care for children.'),
('Oncology', 'Department specializing in cancer treatment and research.'),
('Dermatology', 'Department focusing on skin-related conditions.'),
('Gastroenterology', 'Department dealing with digestive system disorders.'),
('Psychiatry', 'Department providing mental health care and treatment.'),
('Radiology', 'Department specializing in medical imaging and diagnostics.'),
('Emergency Medicine', 'Department providing immediate care for acute illnesses and injuries.')
ON CONFLICT (name) DO NOTHING;  -- Prevents duplicate department names from being inserted

CREATE TABLE IF NOT EXISTS doctors(
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    specialization VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    email VARCHAR(100) UNIQUE,  -- Two doctors cannot share an email
    department_id INTEGER REFERENCES departments(id) ON DELETE SET NULL,
--  If a department is deleted, its doctors stay but department_id becomes NULL
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sample doctors. Department is looked up by name, so the IDs don't need to be known.
INSERT INTO doctors (name, specialization, phone, email, department_id)
SELECT d.name, d.specialization, d.phone, d.email, dep.id
FROM (VALUES
    ('Dr. Ram Sharma',      'Cardiologist',        '9800000001', 'ram.sharma@hospital.com',      'Cardiology'),
    ('Dr. Sita Karki',      'Neurologist',         '9800000002', 'sita.karki@hospital.com',      'Neurology'),
    ('Dr. Hari Thapa',      'Orthopedic Surgeon',  '9800000003', 'hari.thapa@hospital.com',      'Orthopedics'),
    ('Dr. Gita Adhikari',   'Pediatrician',        '9800000004', 'gita.adhikari@hospital.com',   'Pediatrics'),
    ('Dr. Bikash Shrestha', 'Oncologist',          '9800000005', 'bikash.shrestha@hospital.com', 'Oncology'),
    ('Dr. Anita Gurung',    'Dermatologist',       '9800000006', 'anita.gurung@hospital.com',    'Dermatology'),
    ('Dr. Suman Rai',       'Gastroenterologist',  '9800000007', 'suman.rai@hospital.com',       'Gastroenterology'),
    ('Dr. Puja Maharjan',   'Psychiatrist',        '9800000008', 'puja.maharjan@hospital.com',   'Psychiatry'),
    ('Dr. Nabin Poudel',    'Radiologist',         '9800000009', 'nabin.poudel@hospital.com',    'Radiology'),
    ('Dr. Kiran Bhandari',  'Emergency Physician', '9800000010', 'kiran.bhandari@hospital.com',  'Emergency Medicine')
) AS d(name, specialization, phone, email, department_name)
JOIN departments dep ON dep.name = d.department_name
ON CONFLICT (email) DO NOTHING;  -- Re-running the file won't add duplicates


CREATE TABLE IF NOT EXISTS patients(
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    date_of_birth DATE,
    gender VARCHAR(10),
    phone VARCHAR(20),
    email VARCHAR(100),
    address TEXT,
    blood_group VARCHAR(5),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sample patients. Skips a row if a patient with the same phone already exists.
INSERT INTO patients (name, date_of_birth, gender, phone, email, address, blood_group)
SELECT v.name, v.dob::DATE, v.gender, v.phone, v.email, v.address, v.blood_group
FROM (VALUES
    ('Aarav Joshi',     '1990-05-14', 'Male',   '9811000001', 'aarav.joshi@mail.com',     'Kathmandu', 'O+'),
    ('Sneha Pandey',    '1985-11-02', 'Female', '9811000002', 'sneha.pandey@mail.com',    'Lalitpur',  'A+'),
    ('Rohan Basnet',    '2012-03-21', 'Male',   '9811000003', 'rohan.basnet@mail.com',    'Bhaktapur', 'B+'),
    ('Priya Tamang',    '1978-08-30', 'Female', '9811000004', 'priya.tamang@mail.com',    'Pokhara',   'AB+'),
    ('Manish Khadka',   '1965-01-09', 'Male',   '9811000005', 'manish.khadka@mail.com',   'Chitwan',   'O-')
) AS v(name, dob, gender, phone, email, address, blood_group)
WHERE NOT EXISTS (SELECT 1 FROM patients p WHERE p.phone = v.phone);


CREATE TABLE IF NOT EXISTS appointments(
    id SERIAL PRIMARY KEY,
    patient_id INTEGER NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    doctor_id INTEGER NOT NULL REFERENCES doctors(id) ON DELETE CASCADE,
--  If a patient or doctor is deleted, their appointments are deleted too
    appointment_time TIMESTAMP NOT NULL,
    reason TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'scheduled'
        CHECK (status IN ('scheduled', 'completed', 'cancelled')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- A doctor cannot have two active appointments at the same time.
-- Cancelled appointments don't count, so that slot can be booked again.
CREATE UNIQUE INDEX IF NOT EXISTS unique_doctor_slot
    ON appointments (doctor_id, appointment_time)
    WHERE status <> 'cancelled';

-- Sample appointments over the next few days (patients by phone, doctors by email).
INSERT INTO appointments (patient_id, doctor_id, appointment_time, reason)
SELECT p.id, d.id, CURRENT_DATE + v.days * INTERVAL '1 day' + v.at::TIME, v.reason
FROM (VALUES
    ('9811000001', 'ram.sharma@hospital.com',    1, '10:00', 'Chest pain'),
    ('9811000002', 'sita.karki@hospital.com',    1, '11:30', 'Frequent headaches'),
    ('9811000003', 'gita.adhikari@hospital.com', 2, '09:00', 'Routine child checkup'),
    ('9811000004', 'anita.gurung@hospital.com',  2, '14:00', 'Skin rash'),
    ('9811000005', 'hari.thapa@hospital.com',    3, '10:30', 'Knee pain')
) AS v(phone, email, days, at, reason)
JOIN patients p ON p.phone = v.phone
JOIN doctors d ON d.email = v.email
WHERE NOT EXISTS (
    SELECT 1 FROM appointments a WHERE a.patient_id = p.id AND a.doctor_id = d.id
);


CREATE TABLE IF NOT EXISTS users(
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    full_name VARCHAR(100),
    hashed_password TEXT NOT NULL,   -- Never store plain passwords
    role VARCHAR(20) NOT NULL DEFAULT 'staff'
        CHECK (role IN ('admin', 'staff')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
