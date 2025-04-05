# 계정 삭제 API 사용 가이드

이 문서는 클라이언트(안드로이드 앱)에서 사용자 계정 삭제를 요청하는 방법에 대한 가이드입니다.

## API 개요

| 항목 | 설명 |
|------|------|
| 엔드포인트 | `/api/v1/auth/account` |
| HTTP 메서드 | DELETE |
| 인증 | Bearer 토큰 필수 (로그인 상태) |
| 기능 | 현재 로그인한 사용자의 계정과 관련된 모든 데이터 삭제 |

## 요청 형식

### 헤더
```
Authorization: Bearer {access_token}
```

### 요청 본문
요청 본문은 필요 없습니다. 현재 인증된 사용자의 계정이 삭제됩니다.

## 응답 형식

### 성공 응답 (200 OK)
```json
{
  "success": true,
  "message": "계정이 성공적으로 삭제되었습니다.",
  "data": {
    "user_id": "사용자ID",
    "deleted": true
  }
}
```

### 오류 응답

#### 401 Unauthorized (인증 실패)
```json
{
  "detail": "Could not validate credentials"
}
```

#### 404 Not Found (사용자 없음)
```json
{
  "detail": "사용자를 찾을 수 없습니다."
}
```

#### 500 Internal Server Error (서버 오류)
```json
{
  "detail": "계정 삭제 중 오류가 발생했습니다."
}
```