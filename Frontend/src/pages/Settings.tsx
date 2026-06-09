import { useState } from 'react';
import { Settings as SettingsIcon, User, Bell, Shield, Palette } from 'lucide-react';

const tabs = [
  { id: 'profile', label: 'Profile', icon: User },
  { id: 'notifications', label: 'Notifications', icon: Bell },
  { id: 'security', label: 'Security', icon: Shield },
  { id: 'appearance', label: 'Appearance', icon: Palette },
];

export function Settings() {
  const [activeTab, setActiveTab] = useState('profile');

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Settings</h1>
        <p className="text-surface-500 mt-1">Manage your account and application settings</p>
      </div>

      <div className="flex gap-2 border-b border-surface-200 pb-1">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-t-lg transition-colors ${
                activeTab === tab.id
                  ? 'text-primary-600 border-b-2 border-primary-600 bg-primary-50'
                  : 'text-surface-500 hover:text-surface-700 hover:bg-surface-50'
              }`}
            >
              <Icon className="w-4 h-4" />
              {tab.label}
            </button>
          );
        })}
      </div>

      <div className="card">
        <div className="card-body">
          {activeTab === 'profile' && (
            <div className="space-y-4 max-w-lg">
              <h3 className="font-semibold text-lg">Profile Information</h3>
              <div>
                <label className="label">Full Name</label>
                <input type="text" className="input" defaultValue="Admin User" />
              </div>
              <div>
                <label className="label">Email</label>
                <input type="email" className="input" defaultValue="admin@flowforge.io" />
              </div>
              <div>
                <label className="label">Company</label>
                <input type="text" className="input" defaultValue="FlowForge Inc." />
              </div>
              <button className="btn-primary">Save Changes</button>
            </div>
          )}
          {activeTab === 'notifications' && (
            <div className="space-y-4 max-w-lg">
              <h3 className="font-semibold text-lg">Notification Preferences</h3>
              {[
                { label: 'Workflow Executions', desc: 'When a workflow completes or fails' },
                { label: 'Alerts', desc: 'When system alerts are triggered' },
                { label: 'Member Activity', desc: 'When team members take actions' },
                { label: 'Weekly Digest', desc: 'Weekly summary of platform activity' },
              ].map((item) => (
                <div key={item.label} className="flex items-center justify-between py-3 border-b border-surface-100">
                  <div>
                    <p className="font-medium text-sm">{item.label}</p>
                    <p className="text-xs text-surface-500">{item.desc}</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input type="checkbox" className="sr-only peer" defaultChecked />
                    <div className="w-9 h-5 bg-surface-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:bg-primary-600 after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-4 after:w-4 after:transition-all" />
                  </label>
                </div>
              ))}
            </div>
          )}
          {activeTab === 'security' && (
            <div className="space-y-4 max-w-lg">
              <h3 className="font-semibold text-lg">Security Settings</h3>
              <div>
                <label className="label">Current Password</label>
                <input type="password" className="input" placeholder="Enter current password" />
              </div>
              <div>
                <label className="label">New Password</label>
                <input type="password" className="input" placeholder="Enter new password" />
              </div>
              <div>
                <label className="label">Confirm New Password</label>
                <input type="password" className="input" placeholder="Confirm new password" />
              </div>
              <button className="btn-primary">Update Password</button>
            </div>
          )}
          {activeTab === 'appearance' && (
            <div className="space-y-4 max-w-lg">
              <h3 className="font-semibold text-lg">Appearance</h3>
              <div>
                <label className="label">Theme</label>
                <select className="select">
                  <option>Light</option>
                  <option>Dark</option>
                  <option>System</option>
                </select>
              </div>
              <div>
                <label className="label">Font Size</label>
                <select className="select">
                  <option>Small</option>
                  <option selected>Medium</option>
                  <option>Large</option>
                </select>
              </div>
              <button className="btn-primary">Save Preferences</button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}