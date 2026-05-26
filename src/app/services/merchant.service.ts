import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError, map } from 'rxjs/operators';

export interface MerchantProfile {
  organization: string | null;
  name: string | null;
  address: string | null;
  contact_email: string | null;
  phone_number: string | null;
  merchant_id: string | null;
}

export interface ApiResponse {
  message: string;
  type: 'system' | 'success' | 'prompt' | 'error';
  onboarding_complete: boolean;
  backend_payload?: any;
  profile?: MerchantProfile;
}

@Injectable({
  providedIn: 'root'
})
export class MerchantService {
  private apiUrl = 'http://127.0.0.1:5000/api';
  private sessionId: string;

  constructor(private http: HttpClient) {
    this.sessionId = this.generateSessionId();
  }

  private generateSessionId(): string {
    return 'session_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
  }

  sendMessage(userInput: string, action: string = 'message'): Observable<ApiResponse> {
    const payload = {
      message: userInput,
      session_id: this.sessionId,
      action: action
    };
    
    const headers = new HttpHeaders({
      'Content-Type': 'application/json'
    });

    return this.http.post<ApiResponse>(`${this.apiUrl}/chat`, payload, { headers })
      .pipe(
        catchError(error => {
          console.error('API Error:', error);
          return throwError(() => error);
        })
      );
  }

  resetSession(): Observable<any> {
    const payload = {
      session_id: this.sessionId
    };
    
    return this.http.post(`${this.apiUrl}/reset`, payload)
      .pipe(
        catchError(error => {
          console.error('Reset error:', error);
          return throwError(() => error);
        })
      );
  }

  healthCheck(): Observable<any> {
    return this.http.get(`${this.apiUrl}/health`)
      .pipe(
        catchError(error => {
          console.error('Health check failed:', error);
          return throwError(() => error);
        })
      );
  }

  getSessionId(): string {
    return this.sessionId;
  }
}