# 기업용 Claude 스킬 모음

시·공공기관에 제출하는 기업 문서, 디자인, 개발 작업을 위한 Claude 스킬입니다.

| 스킬 | 용도 |
|---|---|
| [gov-submission-docs](skills/gov-submission-docs/SKILL.md) | 사업계획서·제안서·보조금 신청서·결과보고서·공문 작성, 성과지표·통계 근거 정리 |
| [corporate-report-design](skills/corporate-report-design/SKILL.md) | 제안서·보고서·발표 장표·홍보물·웹/앱 화면 디자인 |
| [public-sector-dev-standards](skills/public-sector-dev-standards/SKILL.md) | 공공기관 납품용 소프트웨어 개발·보안·개인정보·접근성·산출물 기준 |

## 설치 방법

### Claude 앱 (claude.ai / 데스크톱)
1. 원하는 스킬 폴더(예: `skills/gov-submission-docs`)를 ZIP으로 압축합니다.
2. Claude 설정 → 스킬(Capabilities) 메뉴에서 ZIP 파일을 업로드합니다.

### Claude Code
스킬 폴더를 아래 위치 중 하나에 복사합니다.
- 모든 프로젝트에서 사용: `~/.claude/skills/`
- 특정 프로젝트에서만 사용: `<프로젝트>/.claude/skills/`

```bash
git clone <이 저장소 주소>
cp -r claude-skills/skills/* ~/.claude/skills/
```

### 다른 에이전트 (Codex, Cursor 등)
```bash
npx skills add <GitHub 아이디>/<저장소 이름>
```

## 회사에 맞게 고치기
각 `SKILL.md`에 회사 CI 색상(HEX), 전용 서체, 자주 쓰는 문서 양식, 주요 발주처를 추가하면 결과물이 더 정확해집니다.

## 주의
- 공고문·과업지시서의 서식과 요구사항이 항상 이 스킬보다 우선합니다.
- 회사 내부 정보나 비밀 값(API 키, 연락처 등)은 이 저장소에 넣지 마세요.
