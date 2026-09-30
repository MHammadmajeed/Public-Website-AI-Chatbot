// src/components/LeadCaptureForm.tsx
import { useState, type FormEvent, type ChangeEvent } from "react";
import { submitLeadCapture, ChatApiError } from "../api/chatClient";
import type { LeadCaptureRequest } from "../types/chat";

interface LeadCaptureFormProps {
  sessionToken: string;
  onSubmitted: () => void;
  onCancel: () => void;
}

interface FormState {
  full_name: string;
  email: string;
  contact_number: string;
  company_name: string;
}

const initialState: FormState = {
  full_name: "",
  email: "",
  contact_number: "",
  company_name: "",
};

function validate(values: FormState): Partial<Record<keyof FormState, string>> {
  const errors: Partial<Record<keyof FormState, string>> = {};

  if (!values.full_name.trim()) {
    errors.full_name = "Please enter your name.";
  } else if (values.full_name.length > 80) {
    errors.full_name = "Name must be under 80 characters.";
  }

  if (!values.email.trim()) {
    errors.email = "Please enter your email.";
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(values.email)) {
    errors.email = "Please enter a valid email address.";
  } else if (values.email.length > 254) {
    errors.email = "Email must be under 254 characters.";
  }

  if (values.contact_number && values.contact_number.length > 20) {
    errors.contact_number = "Contact number must be under 20 characters.";
  }

  if (values.company_name && values.company_name.length > 120) {
    errors.company_name = "Company name must be under 120 characters.";
  }

  return errors;
}

export function LeadCaptureForm({ sessionToken, onSubmitted, onCancel }: LeadCaptureFormProps) {
  const [values, setValues] = useState<FormState>(initialState);
  const [errors, setErrors] = useState<Partial<Record<keyof FormState, string>>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const handleChange = (field: keyof FormState) => (e: ChangeEvent<HTMLInputElement>) => {
    setValues((prev) => ({ ...prev, [field]: e.target.value }));
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setSubmitError(null);

    const validationErrors = validate(values);
    setErrors(validationErrors);
    if (Object.keys(validationErrors).length > 0) return;

    setIsSubmitting(true);
    try {
      const payload: LeadCaptureRequest = {
        session_token: sessionToken,
        full_name: values.full_name.trim(),
        email: values.email.trim(),
        contact_number: values.contact_number.trim() || undefined,
        company_name: values.company_name.trim() || undefined,
      };
      await submitLeadCapture(payload);
      onSubmitted();
    } catch (err) {
      const message =
        err instanceof ChatApiError ? err.message : "Couldn't submit your details. Please try again.";
      setSubmitError(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      aria-label="Share your contact details"
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "10px",
        padding: "12px",
        borderTop: "1px solid #e5e5e5",
        backgroundColor: "#fafafa",
      }}
    >
      <p style={{ margin: 0, fontSize: "13px", color: "#444" }}>
        Share your details and our team will follow up.
      </p>

      <Field
        id="full_name"
        label="Full name"
        value={values.full_name}
        onChange={handleChange("full_name")}
        error={errors.full_name}
        disabled={isSubmitting}
        required
      />
      <Field
        id="email"
        label="Email"
        type="email"
        value={values.email}
        onChange={handleChange("email")}
        error={errors.email}
        disabled={isSubmitting}
        required
      />
      <Field
        id="contact_number"
        label="Phone (optional)"
        value={values.contact_number}
        onChange={handleChange("contact_number")}
        error={errors.contact_number}
        disabled={isSubmitting}
      />
      <Field
        id="company_name"
        label="Company (optional)"
        value={values.company_name}
        onChange={handleChange("company_name")}
        error={errors.company_name}
        disabled={isSubmitting}
      />

      {submitError && (
        <p role="alert" style={{ color: "#dc2626", fontSize: "13px", margin: 0 }}>
          {submitError}
        </p>
      )}

      <div style={{ display: "flex", gap: "8px", marginTop: "4px" }}>
        <button
          type="submit"
          disabled={isSubmitting}
          style={{
            flex: 1,
            padding: "8px 12px",
            borderRadius: "8px",
            border: "none",
            backgroundColor: isSubmitting ? "#93c5fd" : "#2563eb",
            color: "#fff",
            fontSize: "14px",
            cursor: isSubmitting ? "not-allowed" : "pointer",
          }}
        >
          {isSubmitting ? "Submitting…" : "Submit"}
        </button>
        <button
          type="button"
          onClick={onCancel}
          disabled={isSubmitting}
          style={{
            padding: "8px 12px",
            borderRadius: "8px",
            border: "1px solid #ccc",
            backgroundColor: "#fff",
            color: "#333",
            fontSize: "14px",
            cursor: isSubmitting ? "not-allowed" : "pointer",
          }}
        >
          Not now
        </button>
      </div>
    </form>
  );
}

// ---------- Small reusable field ----------

interface FieldProps {
  id: string;
  label: string;
  value: string;
  onChange: (e: ChangeEvent<HTMLInputElement>) => void;
  error?: string;
  disabled?: boolean;
  required?: boolean;
  type?: string;
}

function Field({ id, label, value, onChange, error, disabled, required, type = "text" }: FieldProps) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
      <label htmlFor={id} style={{ fontSize: "12px", color: "#555", fontWeight: 500 }}>
        {label}
        {required ? " *" : ""}
      </label>
      <input
        id={id}
        type={type}
        value={value}
        onChange={onChange}
        disabled={disabled}
        aria-invalid={!!error}
        aria-describedby={error ? `${id}-error` : undefined}
        style={{
          padding: "7px 10px",
          borderRadius: "6px",
          border: error ? "1px solid #dc2626" : "1px solid #ccc",
          fontSize: "14px",
          fontFamily: "inherit",
        }}
      />
      {error && (
        <span id={`${id}-error`} style={{ fontSize: "12px", color: "#dc2626" }}>
          {error}
        </span>
      )}
    </div>
  );
}