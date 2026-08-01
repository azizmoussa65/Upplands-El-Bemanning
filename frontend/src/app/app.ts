import { Component, inject } from '@angular/core';
import { RouterOutlet } from '@angular/router';

import { ThemeService } from './core/theme.service';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet],
  templateUrl: './app.html',
  styleUrl: './app.scss'
})
export class App {
  // Injecte tot pour appliquer le theme (clair/sombre) memorise des le demarrage,
  // avant meme que l'utilisateur se connecte.
  private theme = inject(ThemeService);
}
