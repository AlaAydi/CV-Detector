import { Component, computed, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { AuthBackgroundComponentComponent } from '../../shared/auth-background-component/auth-background-component.component';

interface Feature {
  icon: 'target' | 'check' | 'sparkles' | 'shield';
  title: string;
  description: string;
}

interface Step {
  number: string;
  title: string;
  description: string;
}
@Component({
  selector: 'app-landingpage',
  standalone: true,
  imports: [RouterLink, AuthBackgroundComponentComponent],
  templateUrl: './landingpage.component.html',
  styleUrl: './landingpage.component.scss'
})
export class LandingpageComponent {
 private readonly reducedMotion =
    typeof window !== 'undefined' &&
    !!window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
  currentYear = new Date().getFullYear();

  private rotateX = signal(0);
  private rotateY = signal(0);

  heroTransform = computed(
    () => `perspective(1200px) rotateX(${this.rotateX()}deg) rotateY(${this.rotateY()}deg)`
  );

  features: Feature[] = [
    {
      icon: 'target',
      title: 'Score ATS instantané',
      description:
        "Un score de compatibilité clair entre votre CV et l'offre, calculé en quelques secondes.",
    },
    {
      icon: 'check',
      title: 'Compétences manquantes',
      description: "Repérez immédiatement ce qu'il manque pour matcher parfaitement le poste.",
    },
    {
      icon: 'sparkles',
      title: 'CV optimisé automatiquement',
      description: "Une version reformulée et alignée sur l'offre, prête à télécharger.",
    },
    {
      icon: 'shield',
      title: 'Zéro invention',
      description:
        "Aucune compétence ni expérience n'est ajoutée si elle ne figure pas déjà dans votre CV.",
    },
  ];

  steps: Step[] = [
    { number: '01', title: 'Importer le CV', description: 'PDF ou DOCX, 5 Mo maximum.' },
    {
      number: '02',
      title: 'Coller la description du poste',
      description: "L'IA compare votre profil à l'offre.",
    },
    {
      number: '03',
      title: 'Recevoir le score et le CV optimisé',
      description: 'Score ATS, compétences manquantes, et CV prêt à envoyer.',
    },
  ];

  onHeroMouseMove(event: MouseEvent): void {
    if (this.reducedMotion) return;
    const section = event.currentTarget as HTMLElement;
    const rect = section.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;

    this.rotateX.set(((y - rect.height / 2) / (rect.height / 2)) * -4);
    this.rotateY.set(((x - rect.width / 2) / (rect.width / 2)) * 4);
  }

  onHeroMouseLeave(): void {
    this.rotateX.set(0);
    this.rotateY.set(0);
  }
}
