/**
 * Health AI 사용자 데이터 관리 페이지 스크립트
 */

// API 엔드포인트
const API_BASE_URL = window.location.origin;
const API_ENDPOINTS = {
    verifyToken: '/api/v1/web/auth/verify-token',
    userData: '/api/v1/web/user/data',
    updateProfile: '/api/v1/auth/profile',
    updateHealth: '/api/v1/health/metrics',
    deleteAccount: '/api/v1/auth/account'
};

// DOM 요소
const loginSection = document.getElementById('login-section');
const userDataSection = document.getElementById('user-data-section');
const kakaoLoginBtn = document.getElementById('kakao-login');
const googleLoginBtn = document.getElementById('google-login');
const userId = document.getElementById('user-id');
const userProvider = document.getElementById('user-provider');
const userCreatedAt = document.getElementById('user-created-at');
const userHeight = document.getElementById('user-height');
const userWeight = document.getElementById('user-weight');
const userBmi = document.getElementById('user-bmi');
const profileForm = document.getElementById('profile-form');
const birthDateInput = document.getElementById('birth-date');
const genderSelect = document.getElementById('gender');
const healthForm = document.getElementById('health-form');
const heightInput = document.getElementById('height');
const weightInput = document.getElementById('weight');
const exportDataBtn = document.getElementById('export-data');
const deleteAccountBtn = document.getElementById('delete-account');
const deleteModal = document.getElementById('delete-modal');
const confirmDeleteBtn = document.getElementById('confirm-delete');
const cancelDeleteBtn = document.getElementById('cancel-delete');

// 상태 관리
let currentUser = null;
let authToken = null;

/**
 * 페이지 초기화
 */
function initPage() {
    // 로컬 스토리지에서 토큰 확인
    const token = localStorage.getItem('healthAiToken');
    
    if (token) {
        // 토큰이 있으면 검증 후 사용자 데이터 로드
        authToken = token;
        verifyToken(token)
            .then(userData => {
                if (userData && userData.success) {
                    loadUserData(userData.data.user_id);
                    showUserDataSection();
                } else {
                    showLoginSection();
                }
            })
            .catch(() => {
                // 토큰 검증 실패 시 로그인 화면 표시
                localStorage.removeItem('healthAiToken');
                showLoginSection();
            });
    } else {
        // 토큰이 없으면 로그인 화면 표시
        showLoginSection();
    }
    
    // 이벤트 리스너 설정
    setupEventListeners();
}

/**
 * 이벤트 리스너 설정
 */
function setupEventListeners() {
    // 소셜 로그인 버튼
    kakaoLoginBtn.addEventListener('click', () => handleSocialLogin('kakao'));
    googleLoginBtn.addEventListener('click', () => handleSocialLogin('google'));
    
    // 프로필 폼 제출
    profileForm.addEventListener('submit', handleProfileUpdate);
    
    // 건강 정보 폼 제출
    healthForm.addEventListener('submit', handleHealthUpdate);
    
    // 데이터 내보내기
    exportDataBtn.addEventListener('click', exportUserData);
    
    // 계정 삭제
    deleteAccountBtn.addEventListener('click', showDeleteModal);
    confirmDeleteBtn.addEventListener('click', handleAccountDeletion);
    cancelDeleteBtn.addEventListener('click', hideDeleteModal);
}

/**
 * 로그인 섹션 표시
 */
function showLoginSection() {
    loginSection.classList.remove('hidden');
    userDataSection.classList.add('hidden');
}

/**
 * 사용자 데이터 섹션 표시
 */
function showUserDataSection() {
    loginSection.classList.add('hidden');
    userDataSection.classList.remove('hidden');
}

/**
 * 소셜 로그인 처리
 * @param {string} provider - 소셜 로그인 제공자 (kakao 또는 google)
 */
function handleSocialLogin(provider) {
    // 실제 구현은 각 플랫폼의 SDK를 사용하여 구현
    // 이 코드는 데모용으로, 실제 앱에서는 OAuth 프로세스 구현 필요
    alert(`${provider} 로그인은 네이티브 앱에서만 사용 가능합니다.\n이 웹페이지는 이미 로그인된 사용자를 위한 관리 도구입니다.`);
    
    // 개발 및 테스트 목적으로 토큰을 직접 입력받는 프롬프트 표시
    const token = prompt('개발자 테스트: JWT 토큰을 입력하세요');
    if (token) {
        localStorage.setItem('healthAiToken', token);
        authToken = token;
        
        verifyToken(token)
            .then(userData => {
                if (userData && userData.success) {
                    loadUserData(userData.data.user_id);
                    showUserDataSection();
                } else {
                    alert('유효하지 않은 토큰입니다.');
                    showLoginSection();
                }
            })
            .catch(error => {
                console.error('토큰 검증 오류:', error);
                alert('토큰 검증 중 오류가 발생했습니다.');
                showLoginSection();
            });
    }
}

/**
 * 토큰 검증 API 호출
 * @param {string} token - 검증할 JWT 토큰
 * @returns {Promise<Object>} - 검증 결과 객체
 */
async function verifyToken(token) {
    try {
        const response = await fetch(API_ENDPOINTS.verifyToken, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ token })
        });
        
        return await response.json();
    } catch (error) {
        console.error('토큰 검증 API 오류:', error);
        throw error;
    }
}

/**
 * 사용자 데이터 로드
 * @param {string} userId - 사용자 ID
 */
async function loadUserData(userId) {
    try {
        const response = await fetch(API_ENDPOINTS.userData, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({ user_id: userId })
        });
        
        const userData = await response.json();
        
        if (userData.success) {
            currentUser = userData.data;
            updateUI(currentUser);
        } else {
            console.error('사용자 데이터 로드 실패:', userData.message);
            alert(`데이터 로드 실패: ${userData.message}`);
        }
    } catch (error) {
        console.error('사용자 데이터 로드 API 오류:', error);
        alert('사용자 데이터를 불러오는 중 오류가 발생했습니다.');
    }
}

/**
 * UI 업데이트
 * @param {Object} userData - 사용자 데이터
 */
function updateUI(userData) {
    // 사용자 프로필 정보 업데이트
    userId.textContent = userData.user_id;
    userProvider.textContent = getProviderName(userData.provider);
    userCreatedAt.textContent = formatDate(userData.created_at);
    
    // 개인 정보 폼 업데이트
    if (userData.birth_date) {
        birthDateInput.value = formatDateForInput(userData.birth_date);
    }
    
    if (userData.gender) {
        genderSelect.value = userData.gender;
    }
    
    // 건강 정보 업데이트
    if (userData.health_metrics) {
        const metrics = userData.health_metrics;
        
        if (metrics.height) {
            userHeight.textContent = `${metrics.height} cm`;
            heightInput.value = metrics.height;
        }
        
        if (metrics.weight) {
            userWeight.textContent = `${metrics.weight} kg`;
            weightInput.value = metrics.weight;
        }
        
        // BMI 계산 및 표시
        if (metrics.height && metrics.weight) {
            const height = metrics.height / 100; // cm -> m
            const weight = metrics.weight;
            const bmi = (weight / (height * height)).toFixed(1);
            userBmi.textContent = `${bmi} (${getBmiCategory(bmi)})`;
        }
    }
}

/**
 * 프로필 업데이트 처리
 * @param {Event} event - 폼 제출 이벤트
 */
async function handleProfileUpdate(event) {
    event.preventDefault();
    
    if (!currentUser || !authToken) {
        alert('로그인이 필요합니다.');
        return;
    }
    
    const birthDate = birthDateInput.value;
    const gender = genderSelect.value;
    
    if (!birthDate || !gender) {
        alert('모든 필드를 입력해주세요.');
        return;
    }
    
    try {
        const response = await fetch(API_ENDPOINTS.updateProfile, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({
                birth_date: birthDate,
                gender: gender
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('프로필이 성공적으로 업데이트되었습니다.');
            // 사용자 데이터 다시 로드
            loadUserData(currentUser.user_id);
        } else {
            alert(`프로필 업데이트 실패: ${result.message}`);
        }
    } catch (error) {
        console.error('프로필 업데이트 API 오류:', error);
        alert('프로필 업데이트 중 오류가 발생했습니다.');
    }
}

/**
 * 건강 정보 업데이트 처리
 * @param {Event} event - 폼 제출 이벤트
 */
async function handleHealthUpdate(event) {
    event.preventDefault();
    
    if (!currentUser || !authToken) {
        alert('로그인이 필요합니다.');
        return;
    }
    
    const height = parseFloat(heightInput.value);
    const weight = parseFloat(weightInput.value);
    
    if (isNaN(height) || isNaN(weight)) {
        alert('올바른 키와 몸무게를 입력해주세요.');
        return;
    }
    
    try {
        const response = await fetch(API_ENDPOINTS.updateHealth, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({
                user_id: currentUser.user_id,
                height: height,
                weight: weight
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('건강 정보가 성공적으로 업데이트되었습니다.');
            // 사용자 데이터 다시 로드
            loadUserData(currentUser.user_id);
        } else {
            alert(`건강 정보 업데이트 실패: ${result.message}`);
        }
    } catch (error) {
        console.error('건강 정보 업데이트 API 오류:', error);
        alert('건강 정보 업데이트 중 오류가 발생했습니다.');
    }
}

/**
 * 데이터 내보내기
 */
function exportUserData() {
    if (!currentUser) {
        alert('로그인이 필요합니다.');
        return;
    }
    
    // 현재 사용자 데이터를 JSON 파일로 변환하여 다운로드
    const dataStr = JSON.stringify(currentUser, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    
    const exportFileDefaultName = `healthai-user-data-${currentUser.user_id}.json`;
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
}

/**
 * 계정 삭제 모달 표시
 */
function showDeleteModal() {
    deleteModal.classList.remove('hidden');
}

/**
 * 계정 삭제 모달 숨김
 */
function hideDeleteModal() {
    deleteModal.classList.add('hidden');
}

/**
 * 계정 삭제 처리
 */
async function handleAccountDeletion() {
    if (!currentUser || !authToken) {
        alert('로그인이 필요합니다.');
        hideDeleteModal();
        return;
    }
    
    try {
        const response = await fetch(API_ENDPOINTS.deleteAccount, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('계정이 성공적으로 삭제되었습니다.');
            // 로컬 스토리지 토큰 삭제 및 로그인 화면으로 이동
            localStorage.removeItem('healthAiToken');
            authToken = null;
            currentUser = null;
            hideDeleteModal();
            showLoginSection();
        } else {
            alert(`계정 삭제 실패: ${result.message}`);
            hideDeleteModal();
        }
    } catch (error) {
        console.error('계정 삭제 API 오류:', error);
        alert('계정 삭제 중 오류가 발생했습니다.');
        hideDeleteModal();
    }
}

/**
 * 유틸리티 함수들
 */
function getProviderName(provider) {
    const providers = {
        'kakao': '카카오',
        'google': '구글',
        'apple': '애플'
    };
    
    return providers[provider] || provider;
}

function formatDate(dateString) {
    if (!dateString) return '-';
    
    const date = new Date(dateString);
    return date.toLocaleDateString('ko-KR', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

function formatDateForInput(dateString) {
    if (!dateString) return '';
    
    const date = new Date(dateString);
    return date.toISOString().split('T')[0];
}

function getBmiCategory(bmi) {
    bmi = parseFloat(bmi);
    
    if (bmi < 18.5) return '저체중';
    if (bmi < 23) return '정상';
    if (bmi < 25) return '과체중';
    if (bmi < 30) return '비만';
    return '고도비만';
}

// 페이지 로드 시 초기화
document.addEventListener('DOMContentLoaded', initPage); 