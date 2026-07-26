import { Component, HostListener, input, output, signal } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';

interface NavLink {
  label: string;
  path: string;
}
@Component({
  selector: 'app-header',
  standalone: true,
  imports: [RouterLink, RouterLinkActive],
  templateUrl: './header.component.html',
  styleUrl: './header.component.scss'
})
export class HeaderComponent {
 authenticated = input(false);

  logoutRequested = output<void>();

  scrolled = signal(false);
  menuOpen = signal(false);

  links: NavLink[] = [
    { label: 'Analyser', path: '/analyze' },
    { label: 'Tarifs', path: '/pricing' },
    { label: 'FAQ', path: '/faq' },
  ];

  @HostListener('window:scroll')
  onWindowScroll(): void {
    this.scrolled.set(window.scrollY > 8);
  }

  toggleMenu(): void {
    this.menuOpen.update((open) => !open);
  }

  closeMenu(): void {
    this.menuOpen.set(false);
  }

  logout(): void {
    this.closeMenu();
    this.logoutRequested.emit();
  }
}
