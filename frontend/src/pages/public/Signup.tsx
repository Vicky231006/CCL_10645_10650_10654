import { Link, useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useState } from "react";
import { useAuth } from "../../lib/auth";
import { Alert, Button, Field, Input } from "../../components/ui";
import { ApiError } from "../../lib/api";

const schema = z.object({
  full_name: z.string().max(200).optional(),
  email: z.string().email("Enter a valid email address"),
  password: z.string().min(8, "Use at least 8 characters").max(128),
});

type FormValues = z.infer<typeof schema>;

export function Signup() {
  const { signup } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  async function onSubmit(values: FormValues) {
    setError(null);
    try {
      await signup(values);
      navigate("/app/onboarding", { replace: true });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong. Please try again.");
    }
  }

  return (
    <div className="container-page flex max-w-md flex-col py-16">
      <h1 className="font-serif text-3xl">Create your account</h1>
      <p className="mt-1 text-sm text-ink-muted">
        Free, no billing. You can delete your data at any time.
      </p>
      <form onSubmit={handleSubmit(onSubmit)} className="mt-6 space-y-4" noValidate>
        {error && <Alert tone="error">{error}</Alert>}
        <Field label="Full name" error={errors.full_name?.message} htmlFor="full_name">
          <Input id="full_name" autoComplete="name" {...register("full_name")} />
        </Field>
        <Field label="Email" error={errors.email?.message} htmlFor="email">
          <Input id="email" type="email" autoComplete="email" {...register("email")} />
        </Field>
        <Field label="Password" hint="At least 8 characters." error={errors.password?.message} htmlFor="password">
          <Input id="password" type="password" autoComplete="new-password" {...register("password")} />
        </Field>
        <Button type="submit" loading={isSubmitting} className="w-full">
          Create account
        </Button>
      </form>
      <p className="mt-4 text-sm text-ink-muted">
        Already have an account?{" "}
        <Link to="/login" className="link-quiet">
          Sign in
        </Link>
      </p>
    </div>
  );
}
