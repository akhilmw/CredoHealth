import React, { useEffect, useState } from "react";
import ReactDOM from "react-dom/client";
import "./styles.css";

// API response shapes returned by the FastAPI backend.
type Patient = {
  id: number;
  fhir_id: string;
  given_name: string | null;
  family_name: string | null;
  gender: string | null;
  birth_date: string | null;
  source_updated_at: string | null;
};

type Observation = {
  id: number;
  fhir_id: string;
  code: string | null;
  display: string | null;
  value: string | null;
  unit: string | null;
  status: string | null;
  effective_at: string | null;
};

type PatientDetail = Patient & {
  observations: Observation[];
};

type MigrationResult = {
  patients_seen: number;
  patients_saved: number;
  observations_saved: number;
  failures: string[];
};

// Small fetch wrapper so each API call gets consistent error handling.
async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, options);

  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`);
  }

  return response.json();
}

function fetchPatients() {
  return fetchJson<Patient[]>("/api/patients");
}

function fetchPatient(patientId: number) {
  return fetchJson<PatientDetail>(`/api/patients/${patientId}`);
}

function runMigration(limit: number) {
  return fetchJson<MigrationResult>(`/api/migration/run?limit=${limit}`, {
    method: "POST",
  });
}

function App() {
  // App-level state is enough for this small dashboard.
  const [patients, setPatients] = useState<Patient[]>([]);
  const [selectedPatient, setSelectedPatient] = useState<PatientDetail | null>(
    null,
  );
  const [migrationResult, setMigrationResult] =
    useState<MigrationResult | null>(null);
  const [migrationLimit, setMigrationLimit] = useState(5);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Reloads patients already stored in the local SQLite database.
  async function loadPatients() {
    setLoading(true);
    setError(null);

    try {
      const data = await fetchPatients();
      setPatients(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load patients");
    } finally {
      setLoading(false);
    }
  }

  // Runs a new migration batch, then refreshes the patient list.
  async function handleRunMigration() {
    setLoading(true);
    setError(null);

    try {
      const result = await runMigration(migrationLimit);
      setMigrationResult(result);
      setSelectedPatient(null);
      await loadPatients();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Migration failed");
    } finally {
      setLoading(false);
    }
  }

  // Loads full patient detail only when a user selects a patient.
  async function handleSelectPatient(patientId: number) {
    setLoading(true);
    setError(null);

    try {
      const patient = await fetchPatient(patientId);
      setSelectedPatient(patient);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to load patient detail",
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadPatients();
  }, []);

  return (
    <main className="app-shell">
      <header>
        <h1>Credo Health FHIR Migration</h1>
        <p>Patient migration dashboard</p>
      </header>

      <section className="toolbar">
        <label>
          Limit
          <select
            value={migrationLimit}
            onChange={(event) => setMigrationLimit(Number(event.target.value))}
            disabled={loading}
          >
            {[5, 10, 25, 50, 100].map((limit) => (
              <option key={limit} value={limit}>
                {limit}
              </option>
            ))}
          </select>
        </label>
        <button type="button" onClick={handleRunMigration} disabled={loading}>
          {loading ? "Working..." : "Run Migration"}
        </button>
        <button type="button" onClick={loadPatients} disabled={loading}>
          Refresh Patients
        </button>
      </section>

      {error && <div className="alert">{error}</div>}

      {migrationResult && (
        <section className="summary">
          <strong>Last migration:</strong>
          <span>{migrationResult.patients_seen} seen</span>
          <span>{migrationResult.patients_saved} saved</span>
          <span>{migrationResult.observations_saved} observations</span>
          {migrationResult.failures.length > 0 && (
            <span>{migrationResult.failures.length} failures</span>
          )}
        </section>
      )}

      <section className="content-grid">
        <PatientList
          patients={patients}
          selectedPatientId={selectedPatient?.id ?? null}
          onSelectPatient={handleSelectPatient}
        />
        <PatientDetailView patient={selectedPatient} />
      </section>
    </main>
  );
}

// Left-side list used to select a migrated patient.
type PatientListProps = {
  patients: Patient[];
  selectedPatientId: number | null;
  onSelectPatient: (patientId: number) => void;
};

function PatientList({
  patients,
  selectedPatientId,
  onSelectPatient,
}: PatientListProps) {
  return (
    <section className="panel">
      <h2>Patients</h2>
      {patients.length === 0 ? (
        <p>No patients migrated yet.</p>
      ) : (
        <ul className="patient-list">
          {patients.map((patient) => (
            <li key={patient.id}>
              <button
                type="button"
                className={patient.id === selectedPatientId ? "selected" : ""}
                onClick={() => onSelectPatient(patient.id)}
              >
                <span>{formatPatientName(patient)}</span>
                <small>{patient.fhir_id}</small>
              </button>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

// Right-side detail panel showing demographics and observations.
function PatientDetailView({ patient }: { patient: PatientDetail | null }) {
  if (!patient) {
    return (
      <section className="panel">
        <h2>Patient Detail</h2>
        <p>Select a patient to view observations.</p>
      </section>
    );
  }

  return (
    <section className="panel">
      <h2>{formatPatientName(patient)}</h2>
      <dl className="details">
        <div>
          <dt>FHIR ID</dt>
          <dd>{patient.fhir_id}</dd>
        </div>
        <div>
          <dt>Gender</dt>
          <dd>{patient.gender ?? "Unknown"}</dd>
        </div>
        <div>
          <dt>Birth date</dt>
          <dd>{patient.birth_date ?? "Unknown"}</dd>
        </div>
      </dl>

      <h3>Observations</h3>
      {patient.observations.length === 0 ? (
        <p>No observations found for this patient.</p>
      ) : (
        <div className="observation-list">
          {patient.observations.map((observation) => (
            <article key={observation.id} className="observation">
              <strong>
                {observation.display ?? observation.code ?? "Observation"}
              </strong>
              <span>
                {observation.value ?? "No value"} {observation.unit ?? ""}
              </span>
              <small>{observation.status ?? "Unknown status"}</small>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}

// FHIR names can be partially missing, so build a readable fallback.
function formatPatientName(patient: Patient) {
  const name = [patient.given_name, patient.family_name]
    .filter(Boolean)
    .join(" ");
  return name || "Unnamed patient";
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
