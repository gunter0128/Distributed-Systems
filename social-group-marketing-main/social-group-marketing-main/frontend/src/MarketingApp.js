import React, { useState, useEffect } from 'react';
import { AlertCircle } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from './components/ui/alert';
import api from './api/axios';

// 主應用程序組件
const MarketingApp = () => {
  // 狀態管理
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [rankings, setRankings] = useState([]);
  const [activeTab, setActiveTab] = useState('login');
  const [alert, setAlert] = useState(null);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // 檢查是否已登入
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      setIsLoggedIn(true);
      fetchRankings();
    }
  }, []);

  // 獲取排名數據
  const fetchRankings = async () => {
    try {
      const response = await api.get('/api/rankings');
      setRankings(response.data.rankings);
    } catch (error) {
      showAlert('錯誤', '無法獲取排名數據');
    }
  };

  // 模擬數據獲取
  useEffect(() => {
    if (isLoggedIn) {
      fetchRankings();
      const interval = setInterval(fetchRankings, 1000); // 每30秒更新一次排名
      return () => clearInterval(interval);
    }
  }, [isLoggedIn]);

  // 顯示提示信息
  const showAlert = (title, message) => {
    setAlert({ title, message });
    setTimeout(() => setAlert(null), 3000);
  };

  // 登出功能
  const handleLogout = () => {
    localStorage.removeItem('token');
    setIsLoggedIn(false);
    setRankings([]);
    showAlert('提示', '已登出');
  };

  // 登入表單
  const LoginForm = () => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');

    const handleLogin = async (e) => {
      e.preventDefault();
      try {
        const response = await api.post('/api/login', {
          username,
          password
        });
        
        if (response.status === 200) {
          localStorage.setItem('token', response.data.token);
          setIsLoggedIn(true);
          showAlert('成功', '登入成功！');
        }
      } catch (error) {
        showAlert('錯誤', error.response?.data?.message || '登入失敗，請檢查用戶名和密碼');
      }
    };

    return (
      <form onSubmit={handleLogin} className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-1">用戶名</label>
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="w-full p-2 border rounded"
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">密碼</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full p-2 border rounded"
            required
          />
        </div>
        <button type="submit" className="w-full bg-blue-500 text-white p-2 rounded">
          登入
        </button>
      </form>
    );
  };

  // 排名列表組件
  const RankingList = () => (
    <div className="space-y-4">
      <h2 className="text-xl font-bold">即時排名</h2>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="bg-gray-100">
              <th className="p-2">排名</th>
              <th className="p-2">團隊</th>
              <th className="p-2">分數</th>
            </tr>
          </thead>
          <tbody>
            {rankings.map((team, index) => (
              <tr key={team.team_id} className="border-b">
                <td className="p-2 text-center">{index + 1}</td>
                <td className="p-2 text-center">{team.team_name}</td>
                <td className="p-2 text-center">{team.score.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );

  // 打卡表單組件
  const CheckInForm = () => {
    const [teamId, setTeamId] = useState('');
    const [postUrl, setPostUrl] = useState('');

    const handleCheckIn = async (e) => {
      e.preventDefault();
      try {
        const token = localStorage.getItem('token');
        const response = await api.post('/api/checkin', {
          team_id: teamId,
          post_url: postUrl
        }, {
          headers: {
            'Authorization': `Bearer ${token}`  // 修改這裡：添加 "Bearer " 前綴
          }
        });
        
        if (response.status === 200) {
          showAlert('成功', '打卡成功！');
          setPostUrl('');
          setTeamId('');
          // 重新獲取排名數據
          fetchRankings();
        }
      } catch (error) {
        showAlert('錯誤', error.response?.data?.message || '打卡失敗，請稍後重試');
      }
    };

    return (
      <form onSubmit={handleCheckIn} className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-1">團隊ID</label>
          <input
            type="number"
            value={teamId}
            onChange={(e) => setTeamId(e.target.value)}
            className="w-full p-2 border rounded"
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">貼文連結</label>
          <input
            type="url"
            value={postUrl}
            onChange={(e) => setPostUrl(e.target.value)}
            className="w-full p-2 border rounded"
            required
          />
        </div>
        <button type="submit" className="w-full bg-green-500 text-white p-2 rounded">
          提交打卡
        </button>
      </form>
    );
  };

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div className="container mx-auto p-4">
      {alert && (
        <Alert className="mb-4">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>{alert.title}</AlertTitle>
          <AlertDescription>{alert.message}</AlertDescription>
        </Alert>
      )}
      
      <div className="max-w-4xl mx-auto">
        {!isLoggedIn ? (
          <div className="bg-white p-6 rounded-lg shadow-lg">
            <h1 className="text-2xl font-bold mb-6">揪團按讚行銷活動</h1>
            <LoginForm />
          </div>
        ) : (
          <div className="space-y-8">
            <div className="flex justify-between items-center mb-4">
              <h1 className="text-2xl font-bold">揪團按讚行銷活動</h1>
              <button 
                onClick={handleLogout}
                className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600"
              >
                登出
              </button>
            </div>
            <div className="bg-white p-6 rounded-lg shadow-lg">
              <h2 className="text-xl font-bold mb-4">上傳打卡資料</h2>
              <CheckInForm />
            </div>
            
            <div className="bg-white p-6 rounded-lg shadow-lg">
              <RankingList />
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default MarketingApp;