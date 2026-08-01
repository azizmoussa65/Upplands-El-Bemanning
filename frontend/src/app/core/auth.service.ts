import { HttpClient } from '@angular/common/http';
import { Injectable, inject, signal } from '@angular/core';
import { Observable, catchError, map, of, tap } from 'rxjs';

import { User } from './models';

export const DEFAULT_BRAND_COLOR = '#4f52e5';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private http = inject(HttpClient);
  private base = '/api/auth';

  readonly currentUser = signal<User | null>(null);
  readonly username = signal<string | null>(null);
  readonly checked = signal(false);

  login(username: string, password: string): Observable<User> {
    return this.http
      .post<User>(`${this.base}/login`, { username, password })
      .pipe(tap((res) => this.setUser(res)));
  }

  logout(): Observable<unknown> {
    return this.http.post(`${this.base}/logout`, {}).pipe(tap(() => this.setUser(null)));
  }

  checkAuth(): Observable<boolean> {
    return this.http.get<{ authenticated: boolean } & Partial<User>>(`${this.base}/me`).pipe(
      map((res) => {
        this.setUser(res.authenticated ? (res as unknown as User) : null);
        this.checked.set(true);
        return res.authenticated;
      }),
      catchError(() => {
        this.setUser(null);
        this.checked.set(true);
        return of(false);
      })
    );
  }

  private setUser(user: User | null): void {
    this.currentUser.set(user);
    this.username.set(user?.username ?? null);
    document.documentElement.style.setProperty('--user-color', user?.color || DEFAULT_BRAND_COLOR);
  }
}
