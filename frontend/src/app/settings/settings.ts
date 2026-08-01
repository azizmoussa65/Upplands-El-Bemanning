import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatSnackBar } from '@angular/material/snack-bar';

import { MatButtonToggleModule } from '@angular/material/button-toggle';

import { ApiService } from '../core/api.service';
import { I18nService, Lang } from '../core/i18n.service';
import { AppSettings } from '../core/models';
import { ThemeMode, ThemeService } from '../core/theme.service';

@Component({
  selector: 'app-settings',
  imports: [
    FormsModule,
    MatButtonModule,
    MatButtonToggleModule,
    MatCardModule,
    MatFormFieldModule,
    MatIconModule,
    MatInputModule
  ],
  templateUrl: './settings.html',
  styleUrl: './settings.scss'
})
export class SettingsPage {
  private api = inject(ApiService);
  private snack = inject(MatSnackBar);
  theme = inject(ThemeService);
  i18n = inject(I18nService);

  settings: AppSettings = {
    serperApiKey: '',
    groqApiKey: '',
    defaultIndustryCode: '',
    brevoApiKey: '',
    senderEmail: '',
    senderName: '',
    publicBaseUrl: ''
  };
  saving = signal(false);

  currentPassword = '';
  newPassword = '';
  changingPassword = signal(false);

  constructor() {
    this.api.getSettings().subscribe((s) => (this.settings = s));
  }

  webhookUrl(): string {
    return `${window.location.origin}${this.settings.webhookPath || ''}`;
  }

  saveSettings(): void {
    this.saving.set(true);
    this.api.updateSettings(this.settings).subscribe({
      next: () => {
        this.saving.set(false);
        this.snack.open('Settings saved', 'OK', { duration: 3000 });
      },
      error: () => {
        this.saving.set(false);
        this.snack.open('Error while saving', 'OK', { duration: 4000 });
      }
    });
  }

  changePassword(): void {
    if (!this.currentPassword || !this.newPassword) return;
    this.changingPassword.set(true);
    this.api.changePassword(this.currentPassword, this.newPassword).subscribe({
      next: () => {
        this.changingPassword.set(false);
        this.currentPassword = '';
        this.newPassword = '';
        this.snack.open('Password updated', 'OK', { duration: 3000 });
      },
      error: (err) => {
        this.changingPassword.set(false);
        this.snack.open(err?.error?.error || 'Error', 'OK', { duration: 4000 });
      }
    });
  }
}
