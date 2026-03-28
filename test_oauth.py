#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Google OAuth 설정 및 토큰 테스트"""

import sys
import os
sys.path.insert(0, '.')

print("="*60)
print("Google OAuth 설정 확인")
print("="*60)

try:
    from auth import CLIENT_CONFIG, get_flow, SCOPES
    
    print("\n✓ 1. 모듈 로드 성공")
    
    # 설정 확인
    web_config = CLIENT_CONFIG["web"]
    print(f"\n✓ 2. 클라이언트 설정:")
    print(f"   - Client ID: {web_config['client_id'][:30]}...")
    print(f"   - 토큰 URI: {web_config['token_uri']}")
    print(f"   - Redirect URIs: {web_config['redirect_uris']}")
    print(f"   - Scopes: {SCOPES}")
    
    # Flow 생성 시도
    print(f"\n✓ 3. OAuth Flow 생성 시도...")
    flow = get_flow()
    print(f"   - Flow 객체 생성 성공")
    print(f"   - Flow client ID: {flow.client_id[:30]}...")
    
    # 인증 URL 생성 시도
    print(f"\n✓ 4. 인증 URL 생성 시도...")
    auth_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )
    print(f"   - 인증 URL 생성 성공 (길이: {len(auth_url)}자)")
    print(f"   - URL (처음 80자): {auth_url[:80]}...")
    
    print("\n" + "="*60)
    print("✅ 모든 설정이 정상입니다!")
    print("="*60)
    
except Exception as e:
    print("\n" + "="*60)
    print(f"❌ 오류 발생:")
    print("="*60)
    print(f"오류 타입: {type(e).__name__}")
    print(f"오류 메시지: {str(e)}")
    print("\n" + "-"*60)
    import traceback
    traceback.print_exc()
    print("-"*60)
