import { useState, useEffect } from 'react';
import { EyeIcon, ArrowDownTrayIcon, TrashIcon } from '@heroicons/react/24/outline';
import Layout from '../components/Layout';
import CertificateModal from '../components/CertificateModal';
import DeleteConfirmModal from '../components/DeleteConfirmModal';
import { devicesAPI } from '../utils/api';

const Devices = () => {
  const [devices, setDevices] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [modalOpen, setModalOpen] = useState(false);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [selectedDevice, setSelectedDevice] = useState(null);
  const [deviceToDelete, setDeviceToDelete] = useState(null);
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    fetchDevices();
  }, []);

  const fetchDevices = async () => {
    try {
      setIsLoading(true);
      const response = await devicesAPI.list();
      setDevices(response.data);
    } catch (err) {
      setError('Failed to fetch devices');
    } finally {
      setIsLoading(false);
    }
  };

  const handleViewCertificate = async (device) => {
    try {
      const response = await devicesAPI.view(device.id, 'device_cert');
      setSelectedDevice({
        ...device,
        certText: response.data.cert_text,
      });
      setModalOpen(true);
    } catch (err) {
      setError('Failed to fetch certificate');
    }
  };

  const handleDownload = async (device) => {
    try {
      const response = await devicesAPI.download(device.id);
      const blob = new Blob([response.data], { type: 'application/zip' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${device.name}_certificates.zip`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError('Failed to download certificate');
    }
  };

  const handleDeleteDevice = (device) => {
    setDeviceToDelete(device);
    setDeleteModalOpen(true);
    setError('');
  };

  const confirmDelete = async (password) => {
    if (!deviceToDelete) return;

    setIsDeleting(true);
    try {
      await devicesAPI.delete(deviceToDelete.id, password);
      
      // Remove device from state
      setDevices(devices.filter(d => d.id !== deviceToDelete.id));
      
      // Close modal
      setDeleteModalOpen(false);
      setDeviceToDelete(null);
      
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to delete device');
    } finally {
      setIsDeleting(false);
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (isLoading) {
    return (
      <Layout currentPage="Devices">
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout currentPage="Devices">
      <div className="px-4 sm:px-6 lg:px-8">
        <div className="sm:flex sm:items-center">
          <div className="sm:flex-auto">
            <h1 className="text-2xl font-semibold text-gray-900">Device Certificates</h1>
            <p className="mt-2 text-sm text-gray-700">
              View and manage all generated device certificates
            </p>
          </div>
        </div>

        {error && (
          <div className="mt-4 rounded-md bg-red-50 p-4">
            <div className="text-sm text-red-700">{error}</div>
          </div>
        )}

        <div className="mt-8 flow-root">
          <div className="-mx-4 -my-2 overflow-x-auto sm:-mx-6 lg:-mx-8">
            <div className="inline-block min-w-full py-2 align-middle sm:px-6 lg:px-8">
              {devices.length === 0 ? (
                <div className="text-center py-12">
                  <div className="text-gray-500">
                    <p className="text-lg">No devices found</p>
                    <p className="text-sm mt-2">Generate your first device certificate from the dashboard</p>
                  </div>
                </div>
              ) : (
                <div className="overflow-hidden shadow ring-1 ring-black ring-opacity-5 md:rounded-lg">
                  <table className="min-w-full divide-y divide-gray-300">
                    <thead className="bg-gray-50">
                      <tr>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Device Name
                        </th>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Created At
                        </th>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Actions
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {devices.map((device) => (
                        <tr key={device.id} className="hover:bg-gray-50">
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="text-sm font-medium text-gray-900">
                              {device.name}
                            </div>
                            <div className="text-sm text-gray-500">
                              ID: {device.id}
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {formatDate(device.created_at)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                            <div className="flex space-x-2">
                              <button
                                onClick={() => handleViewCertificate(device)}
                                className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                              >
                                <EyeIcon className="h-4 w-4 mr-1" />
                                View
                              </button>
                              <button
                                onClick={() => handleDownload(device)}
                                className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                              >
                                <ArrowDownTrayIcon className="h-4 w-4 mr-1" />
                                Download
                              </button>
                              <button
                                onClick={() => handleDeleteDevice(device)}
                                className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                              >
                                <TrashIcon className="h-4 w-4 mr-1" />
                                Delete
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Certificate Modal */}
        {selectedDevice && (
          <CertificateModal
            isOpen={modalOpen}
            onClose={() => {
              setModalOpen(false);
              setSelectedDevice(null);
            }}
            deviceId={selectedDevice.id}
            deviceName={selectedDevice.name}
            initialCertText={selectedDevice.certText}
          />
        )}

        {/* Delete Confirmation Modal */}
        <DeleteConfirmModal
          isOpen={deleteModalOpen}
          onClose={() => {
            setDeleteModalOpen(false);
            setDeviceToDelete(null);
            setError('');
          }}
          onConfirm={confirmDelete}
          deviceName={deviceToDelete?.name || ''}
          isLoading={isDeleting}
        />
      </div>
    </Layout>
  );
};

export default Devices;
