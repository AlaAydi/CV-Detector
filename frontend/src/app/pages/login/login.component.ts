import { Component, computed, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { AuthService } from '../../core/services/auth.service';
import { AuthBackgroundComponentComponent } from '../../shared/auth-background-component/auth-background-component.component';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [
    ReactiveFormsModule,
    RouterLink,
    MatCardModule,
    MatFormFieldModule,
    MatInputModule,
    MatButtonModule,
    AuthBackgroundComponentComponent,
  ],
  templateUrl: './login.component.html',
  styleUrl: './login.component.scss',
})
export class LoginComponent {
  private fb = inject(FormBuilder);
  private auth = inject(AuthService);
  private router = inject(Router);

  error = '';
  loading = false;

  private readonly reducedMotion =
    typeof window !== 'undefined' &&
    !!window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;

  // 3D tilt state, driven by the pointer position over the card
  private rotateX = signal(0);
  private rotateY = signal(0);
  private glowX = signal(50);
  private glowY = signal(50);

  cardTransform = computed(
    () => `perspective(1000px) rotateX(${this.rotateX()}deg) rotateY(${this.rotateY()}deg)`
  );
  glowBackground = computed(
    () =>
      `radial-gradient(circle at ${this.glowX()}% ${this.glowY()}%, rgba(124, 111, 240, 0.35), transparent 60%)`
  );

  form = this.fb.group({
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(6)]],
  });

  onCardMouseMove(event: MouseEvent): void {
    if (this.reducedMotion) return;

    const card = event.currentTarget as HTMLElement;
    const rect = card.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;

    this.rotateX.set(((y - rect.height / 2) / (rect.height / 2)) * -6);
    this.rotateY.set(((x - rect.width / 2) / (rect.width / 2)) * 6);
    this.glowX.set((x / rect.width) * 100);
    this.glowY.set((y / rect.height) * 100);
  }

  onCardMouseLeave(): void {
    this.rotateX.set(0);
    this.rotateY.set(0);
    this.glowX.set(50);
    this.glowY.set(50);
  }

  submit(): void {
    if (this.form.invalid) return;
    this.loading = true;
    this.error = '';

    const { email, password } = this.form.getRawValue();
    this.auth.login(email!, password!).subscribe({
      next: () => {
        this.loading = false;
        this.router.navigate(['/dashboard']);
      },
      error: () => {
        this.loading = false;
        this.error = 'Email ou mot de passe incorrect.';
      },
    });
  }
}
