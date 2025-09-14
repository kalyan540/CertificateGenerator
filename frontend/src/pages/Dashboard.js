import { useState } from 'react';
import { PlusIcon, ShieldCheckIcon } from '@heroicons/react/24/outline';
import Layout from '../components/Layout';
import CertificateModal from '../components/CertificateModal';
import { devicesAPI } from '../utils/api';

const Dashboard = () => {
  const [formData, setFormData] = useState({ name: '' });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [modalOpen, setModalOpen] = useState(false);
  const [certificateData, setCertificateData] = useState(null);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
    setError('');
    setSuccess('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');
    setSuccess('');

    try {
      const response = await devicesAPI.create(formData);
      setCertificateData({
        deviceName: response.data.device.name,
        certText: response.data.cert_text,
        deviceId: response.data.device.id,
      });
      setModalOpen(true);
      setSuccess(response.data.message);
      setFormData({ name: '' });
    } catch (err) {
      setError(
        err.response?.data?.detail || 'Failed to generate certificate'
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleDownload = async () => {
    if (!certificateData) return;

    try {
      const response = await devicesAPI.download(certificateData.deviceId);
      const blob = new Blob([response.data], { type: 'application/zip' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${certificateData.deviceName}_certificates.zip`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError('Failed to download certificate');
    }
  };

  return (
    <Layout currentPage="Dashboard">
      <div className="px-4 sm:px-6 lg:px-8">
        <div className="sm:flex sm:items-center">
          <div className="sm:flex-auto">
            <h1 className="text-2xl font-semibold text-gray-900">Dashboard</h1>
            <p className="mt-2 text-sm text-gray-700">
              Generate new device certificates for your IoT devices
            </p>
          </div>
        </div>

        <div className="mt-8 grid grid-cols-1 gap-6 lg:grid-cols-2">
          {/* Certificate Generation Form */}
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                Generate Device Certificate
              </h3>
              
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label htmlFor="name" className="block text-sm font-medium text-gray-700">
                    Device Name
                  </label>
                  <div className="mt-1">
                    <input
                      type="text"
                      name="name"
                      id="name"
                      required
                      pattern="[a-zA-Z0-9_-]+"
                      title="Only alphanumeric characters, hyphens, and underscores are allowed"
                      className="shadow-sm focus:ring-primary-500 focus:border-primary-500 block w-full sm:text-sm border-gray-300 rounded-md"
                      placeholder="e.g., device01, sensor-temp-01"
                      value={formData.name}
                      onChange={handleChange}
                      disabled={isLoading}
                    />
                  </div>
                  <p className="mt-1 text-xs text-gray-500">
                    Only alphanumeric characters, hyphens, and underscores allowed (no spaces)
                  </p>
                </div>

                {error && (
                  <div className="rounded-md bg-red-50 p-4">
                    <div className="text-sm text-red-700">{error}</div>
                  </div>
                )}

                {success && (
                  <div className="rounded-md bg-green-50 p-4">
                    <div className="text-sm text-green-700">{success}</div>
                  </div>
                )}

                <div className="flex space-x-3">
                  <button
                    type="submit"
                    disabled={isLoading || !formData.name.trim()}
                    className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <PlusIcon className="h-4 w-4 mr-2" />
                    {isLoading ? 'Generating...' : 'Generate Certificate'}
                  </button>
                </div>
              </form>
            </div>
          </div>

          {/* Quick Stats */}
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                Certificate Information
              </h3>
              
              <div className="space-y-4">
                <div className="flex items-center">
                  <ShieldCheckIcon className="h-5 w-5 text-green-500 mr-2" />
                  <span className="text-sm text-gray-700">Root CA Required in /certs folder</span>
                </div>
                
                <div className="text-sm text-gray-600 space-y-2">
                  <p><strong>Certificate Validity:</strong> 1 Year (365 days)</p>
                  <p><strong>Key Size:</strong> 2048 bits RSA</p>
                  <p><strong>Organization:</strong> Prahari Technologies</p>
                  <p><strong>Location:</strong> Vadodara, Gujarat, IN</p>
                </div>

                <div className="border-t border-gray-200 pt-4">
                  <h4 className="text-sm font-medium text-gray-900 mb-2">Generated Files:</h4>
                  <ul className="text-xs text-gray-600 space-y-1">
                    <li>• Device Certificate (.crt)</li>
                    <li>• Device Private Key (.key)</li>
                    <li>• Certificate Bundle (.bundle.crt)</li>
                    <li>• Usage Instructions (.txt)</li>
                    <li>• Root CA Certificate (.crt)</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Certificate Modal */}
        {certificateData && (
          <CertificateModal
            isOpen={modalOpen}
            onClose={() => setModalOpen(false)}
            deviceId={certificateData.deviceId}
            deviceName={certificateData.deviceName}
            initialCertText={certificateData.certText}
          />
        )}

        {/* Download Button in Modal */}
        {modalOpen && certificateData && (
          <div className="fixed bottom-6 right-6 z-20">
            <button
              onClick={handleDownload}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-lg text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
            >
              Download ZIP
            </button>
          </div>
        )}
      </div>
    </Layout>
  );
};

export default Dashboard;
