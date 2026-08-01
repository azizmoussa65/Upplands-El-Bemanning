import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatSnackBar } from '@angular/material/snack-bar';
import { MatTableModule } from '@angular/material/table';

import { ApiService } from '../core/api.service';
import { AuthService } from '../core/auth.service';
import { User } from '../core/models';

@Component({
  selector: 'app-users-list',
  imports: [
    FormsModule,
    MatButtonModule,
    MatCardModule,
    MatFormFieldModule,
    MatIconModule,
    MatInputModule,
    MatTableModule
  ],
  templateUrl: './users-list.html',
  styleUrl: './users-list.scss'
})
export class UsersList {
  private api = inject(ApiService);
  private snack = inject(MatSnackBar);
  auth = inject(AuthService);

  readonly columns = ['avatar', 'color', 'username', 'email', 'actions'];

  users = signal<User[]>([]);
  creating = signal(false);
  uploadingId = signal<string | null>(null);

  newUsername = '';
  newPassword = '';
  newEmail = '';
  newColor = '#2e9e5b';

  constructor() {
    this.refresh();
  }

  refresh(): void {
    this.api.getUsers().subscribe((users) => this.users.set(users));
  }

  createUser(): void {
    if (!this.newUsername || this.newPassword.length < 6) {
      this.snack.open('Username required, password must be at least 6 characters', 'OK', { duration: 4000 });
      return;
    }
    this.creating.set(true);
    this.api.createUser(this.newUsername, this.newPassword, this.newEmail, this.newColor).subscribe({
      next: () => {
        this.creating.set(false);
        this.newUsername = '';
        this.newPassword = '';
        this.newEmail = '';
        this.refresh();
      },
      error: (err) => {
        this.creating.set(false);
        this.snack.open(err?.error?.error || 'Could not create user', 'OK', { duration: 4000 });
      }
    });
  }

  updateColor(user: User, color: string): void {
    this.api.updateUser(user.id, { color }).subscribe(() => this.refresh());
  }

  onAvatarSelected(user: User, event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    input.value = '';
    if (!file) return;

    this.uploadingId.set(user.id);
    this.api.uploadAvatar(user.id, file).subscribe({
      next: () => {
        this.uploadingId.set(null);
        this.refresh();
      },
      error: (err) => {
        this.uploadingId.set(null);
        this.snack.open(err?.error?.error || 'Could not upload photo', 'OK', { duration: 4000 });
      }
    });
  }

  initials(user: User): string {
    return user.username.slice(0, 2).toUpperCase();
  }

  deleteUser(user: User): void {
    this.api.deleteUser(user.id).subscribe({
      next: () => this.refresh(),
      error: (err) => this.snack.open(err?.error?.error || 'Could not delete user', 'OK', { duration: 4000 })
    });
  }
}
