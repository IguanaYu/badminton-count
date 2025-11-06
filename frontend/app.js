const API_BASE = '/api';
const state = {
  token: localStorage.getItem('badminton_token'),
  currentUser: null,
  users: [],
  matches: [],
  rankings: [],
};

const loginSection = document.getElementById('login-section');
const loginForm = document.getElementById('login-form');
const loginError = document.getElementById('login-error');
const appSection = document.getElementById('app-section');
const userInfo = document.getElementById('user-info');
const tabs = document.querySelectorAll('.tab');
const matchesList = document.getElementById('matches-list');
const onlyMineCheckbox = document.getElementById('only-mine');
const addMatchBtn = document.getElementById('add-match-btn');
const matchDialog = document.getElementById('match-dialog');
const matchDialogTitle = document.getElementById('match-dialog-title');
const matchDialogBody = document.getElementById('match-dialog-body');
const closeMatchDialog = document.getElementById('close-match-dialog');
const matchFormDialog = document.getElementById('match-form-dialog');
const matchForm = document.getElementById('match-form');
const closeMatchFormBtn = document.getElementById('close-match-form');
const matchTypeSelect = document.getElementById('match-type');
const sideAContainer = document.getElementById('side-a');
const sideBContainer = document.getElementById('side-b');
const rankingsTableBody = document.querySelector('#rankings-table tbody');
const playerDetail = document.getElementById('player-detail');
const profileBox = document.getElementById('profile');
const exportMyMatchesBtn = document.getElementById('export-my-matches');
const exportMySummaryBtn = document.getElementById('export-my-summary');
const exportAllBtn = document.getElementById('export-all');
const adminPanel = document.getElementById('admin-panel');
const rootPanel = document.getElementById('root-panel');
const createUserForm = document.getElementById('create-user-form');

async function apiFetch(path, options = {}) {
  const headers = options.headers ? { ...options.headers } : {};
  if (state.token) {
    headers['Authorization'] = `Bearer ${state.token}`;
  }
  if (options.body && !(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });
  if (response.status === 401) {
    logout();
    throw new Error('登录已过期，请重新登录');
  }
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || '请求失败');
  }
  if (response.status === 204) {
    return null;
  }
  const contentType = response.headers.get('content-type') || '';
  if (contentType.includes('application/json')) {
    return response.json();
  }
  return response;
}

function setToken(token) {
  state.token = token;
  if (token) {
    localStorage.setItem('badminton_token', token);
  } else {
    localStorage.removeItem('badminton_token');
  }
}

function logout() {
  setToken(null);
  state.currentUser = null;
  loginSection.classList.remove('hidden');
  appSection.classList.add('hidden');
  userInfo.textContent = '';
}

loginForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  loginError.textContent = '';
  const formData = new FormData(loginForm);
  const username = formData.get('username');
  const password = formData.get('password');
  try {
    const response = await fetch(`${API_BASE}/auth/token`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ username, password }),
    });
    if (!response.ok) {
      throw new Error('登录失败，请检查用户名或密码');
    }
    const data = await response.json();
    setToken(data.access_token);
    await initializeApp();
  } catch (error) {
    loginError.textContent = error.message;
  }
});

closeMatchDialog.addEventListener('click', () => matchDialog.close());
closeMatchFormBtn.addEventListener('click', () => matchFormDialog.close());

onlyMineCheckbox.addEventListener('change', () => loadMatches(onlyMineCheckbox.checked));
addMatchBtn.addEventListener('click', () => {
  matchForm.reset();
  updateMatchFormPlayers();
  matchFormDialog.showModal();
});

matchTypeSelect.addEventListener('change', updateMatchFormPlayers);

matchForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const formData = new FormData(matchForm);
  const payload = {
    played_at: new Date(formData.get('played_at')).toISOString(),
    session_number: formData.get('session_number') ? Number(formData.get('session_number')) : null,
    match_type: formData.get('match_type'),
    side_a_players: collectPlayers(sideAContainer),
    side_b_players: collectPlayers(sideBContainer),
    score_a: Number(formData.get('score_a')),
    score_b: Number(formData.get('score_b')),
    notes: formData.get('notes') || null,
  };

  try {
    await apiFetch('/matches/', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    matchFormDialog.close();
    await loadMatches(onlyMineCheckbox.checked);
    alert('比赛录入成功');
  } catch (error) {
    alert(`录入失败：${error.message}`);
  }
});

createUserForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const formData = new FormData(createUserForm);
  const payload = {
    username: formData.get('username'),
    full_name: formData.get('full_name'),
    gender: formData.get('gender'),
    password: formData.get('password'),
    can_record: formData.get('can_record') === 'on',
    is_admin: formData.get('is_admin') === 'on',
  };
  try {
    await apiFetch('/users/', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    alert('用户创建成功');
    createUserForm.reset();
    await loadUsers();
    await loadRankings();
  } catch (error) {
    alert(`创建失败：${error.message}`);
  }
});

exportMyMatchesBtn.addEventListener('click', () => downloadFile('/exports/me/matches', `${state.currentUser.username}_matches.xlsx`));
exportMySummaryBtn.addEventListener('click', () => downloadFile('/exports/me/summary', `${state.currentUser.username}_summary.xlsx`));
exportAllBtn.addEventListener('click', () => downloadFile('/exports/all', 'all_matches.xlsx'));

function downloadFile(path, filename) {
  apiFetch(path)
    .then((response) => response.blob())
    .then((blob) => {
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    })
    .catch((error) => alert(`导出失败：${error.message}`));
}

function collectPlayers(container) {
  return Array.from(container.querySelectorAll('select')).map((select) => Number(select.value));
}

function updateMatchFormPlayers() {
  const matchType = matchTypeSelect.value;
  const requirements = {
    singles: [1, 1],
    doubles: [2, 2],
    one_vs_two: [1, 2],
  };
  const [sideACount, sideBCount] = requirements[matchType];
  renderPlayerSelectors(sideAContainer, sideACount);
  renderPlayerSelectors(sideBContainer, sideBCount);
}

function renderPlayerSelectors(container, count) {
  container.innerHTML = '';
  if (!state.users.length) {
    container.innerHTML = '<p class="hint">请先创建选手</p>';
    return;
  }
  for (let i = 0; i < count; i += 1) {
    const wrapper = document.createElement('label');
    wrapper.textContent = `选手 ${i + 1}`;
    const select = document.createElement('select');
    select.required = true;
    state.users.forEach((user) => {
      const option = document.createElement('option');
      option.value = user.id;
      option.textContent = user.full_name;
      select.appendChild(option);
    });
    wrapper.appendChild(select);
    container.appendChild(wrapper);
  }
}

function formatDateTime(value) {
  const date = new Date(value);
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(
    date.getDate()
  ).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`;
}

async function loadMatches(onlyMine = false) {
  try {
    const data = await apiFetch(`/matches/?only_mine=${onlyMine}`);
    state.matches = data.matches;
    renderMatches();
  } catch (error) {
    alert(`获取比赛列表失败：${error.message}`);
  }
}

function renderMatches() {
  matchesList.innerHTML = '';
  if (!state.matches.length) {
    matchesList.innerHTML = '<p class="hint">暂无比赛记录</p>';
    return;
  }
  state.matches.forEach((match) => {
    const card = document.createElement('div');
    card.className = 'match-card';
    card.innerHTML = `
      <div class="match-meta">
        <span>${formatDateTime(match.played_at)}</span>
        <span>${match.match_type === 'singles' ? '单打' : match.match_type === 'doubles' ? '双打' : '1 v 2'}</span>
      </div>
      <div><strong>比分：</strong> A ${match.score_a} - B ${match.score_b}</div>
      <div><strong>胜者：</strong> ${match.winner_side === 'A' ? 'A 方' : 'B 方'}</div>
    `;
    card.addEventListener('click', () => openMatchDialog(match.id));
    matchesList.appendChild(card);
  });
}

async function openMatchDialog(matchId) {
  try {
    const match = await apiFetch(`/matches/${matchId}`);
    matchDialogTitle.textContent = `比赛 #${match.id}`;
    const players = match.participants
      .map((p) => `${p.side} 方 ${p.slot}: ${p.full_name}`)
      .join('<br />');
    matchDialogBody.innerHTML = `
      <div class="dialog-list">
        <div><strong>时间：</strong>${formatDateTime(match.played_at)}</div>
        <div><strong>类型：</strong>${match.match_type}</div>
        <div><strong>比分：</strong>A ${match.score_a} - B ${match.score_b}</div>
        <div><strong>胜者：</strong>${match.winner_side === 'A' ? 'A 方' : 'B 方'}</div>
        <div><strong>录入人：</strong>${match.recorded_by}</div>
        <div><strong>选手：</strong><br />${players}</div>
        ${match.notes ? `<div><strong>备注：</strong>${match.notes}</div>` : ''}
      </div>
    `;
    matchDialog.showModal();
  } catch (error) {
    alert(`获取比赛详情失败：${error.message}`);
  }
}

async function loadRankings() {
  try {
    const rankings = await apiFetch('/stats/rankings');
    state.rankings = rankings;
    renderRankings();
  } catch (error) {
    alert(`获取排行榜失败：${error.message}`);
  }
}

function renderRankings() {
  rankingsTableBody.innerHTML = '';
  state.rankings.forEach((row) => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${row.full_name}</td>
      <td>${(row.win_rate * 100).toFixed(1)}%</td>
      <td>${row.wins} 胜 ${row.losses} 负</td>
    `;
    tr.addEventListener('click', () => loadPlayerDetail(row.user_id));
    rankingsTableBody.appendChild(tr);
  });
}

async function loadPlayerDetail(userId) {
  try {
    const detail = await apiFetch(`/stats/players/${userId}`);
    renderPlayerDetail(detail);
  } catch (error) {
    alert(`获取选手详情失败：${error.message}`);
  }
}

function renderPlayerDetail(detail) {
  const { user, total_matches, wins, losses, win_rate, singles, doubles, one_vs_two_as_one, one_vs_two_as_two, teammates, calendar } = detail;
  const categories = [
    ['单打胜率', singles],
    ['双打胜率', doubles],
    ['1v2 担任 1 方', one_vs_two_as_one],
    ['1v2 担任 2 方', one_vs_two_as_two],
  ];

  const categoryHtml = categories
    .map(
      ([label, stats]) => `
        <div>
          <strong>${label}</strong><br />
          ${stats.matches} 场，${stats.wins} 胜 ${stats.losses} 负，胜率 ${(stats.win_rate * 100).toFixed(1)}%
        </div>
      `
    )
    .join('');

  const teammateHtml = teammates.length
    ? `
    <h4>最佳队友</h4>
    <ul>
      ${teammates
        .map(
          (mate) => `
            <li>${mate.full_name}：${mate.matches} 场，${mate.wins} 胜 ${mate.losses} 负，胜率 ${(mate.win_rate * 100).toFixed(1)}%</li>
          `
        )
        .join('')}
    </ul>`
    : '<p class="hint">暂无队友数据</p>';

  const calendarHtml = calendar.length
    ? `<div class="tag-list">${calendar.map((day) => `<span>${day}</span>`).join('')}</div>`
    : '<p class="hint">最近暂无打球记录</p>';

  playerDetail.innerHTML = `
    <div class="stat-grid">
      <div><strong>${user.full_name}</strong>（用户名：${user.username}）</div>
      <div><strong>总战绩：</strong>${total_matches} 场，${wins} 胜 ${losses} 负，胜率 ${(win_rate * 100).toFixed(1)}%</div>
      ${categoryHtml}
      ${teammateHtml}
      <h4>打球日历</h4>
      ${calendarHtml}
    </div>
  `;
}

async function loadProfile() {
  try {
    const me = await apiFetch('/users/me');
    state.currentUser = me;
    userInfo.textContent = `${me.full_name}（${me.username}）`;
    profileBox.innerHTML = `
      <p><strong>姓名：</strong>${me.full_name}</p>
      <p><strong>用户名：</strong>${me.username}</p>
      <p><strong>性别：</strong>${translateGender(me.gender)}</p>
      <p><strong>录入权限：</strong>${me.can_record || me.is_admin ? '是' : '否'}</p>
      <p><strong>管理员：</strong>${me.is_admin ? '是' : '否'}</p>
    `;
    if (me.is_admin) {
      adminPanel.classList.remove('hidden');
      addMatchBtn.classList.remove('hidden');
    }
    if (me.can_record || me.is_admin) {
      addMatchBtn.classList.remove('hidden');
    }
    if (me.is_root) {
      rootPanel.classList.remove('hidden');
    }
  } catch (error) {
    alert(`加载个人信息失败：${error.message}`);
  }
}

function translateGender(value) {
  switch (value) {
    case 'male':
      return '男';
    case 'female':
      return '女';
    default:
      return '其他';
  }
}

async function loadUsers() {
  const data = await apiFetch('/users/');
  state.users = data.users;
  updateMatchFormPlayers();
}

function setupTabs() {
  tabs.forEach((tab) => {
    tab.addEventListener('click', () => {
      tabs.forEach((t) => t.classList.remove('active'));
      tab.classList.add('active');
      document.querySelectorAll('.tab-content').forEach((section) => section.classList.add('hidden'));
      document.getElementById(tab.dataset.target).classList.remove('hidden');
      if (tab.dataset.target === 'matches-view') {
        loadMatches(onlyMineCheckbox.checked);
      } else if (tab.dataset.target === 'players-view') {
        loadRankings();
      }
    });
  });
}

async function initializeApp() {
  loginSection.classList.add('hidden');
  appSection.classList.remove('hidden');
  adminPanel.classList.add('hidden');
  rootPanel.classList.add('hidden');
  addMatchBtn.classList.add('hidden');
  await Promise.all([loadProfile(), loadUsers(), loadMatches(false), loadRankings()]);
}

function autoLogin() {
  if (!state.token) {
    loginSection.classList.remove('hidden');
    appSection.classList.add('hidden');
    return;
  }
  initializeApp().catch(() => logout());
}

setupTabs();
autoLogin();
