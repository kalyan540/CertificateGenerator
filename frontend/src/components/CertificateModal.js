import { useState, useEffect } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { Fragment } from 'react';
import { XMarkIcon, ClipboardDocumentIcon, CheckIcon } from '@heroicons/react/24/outline';
import { devicesAPI } from '../utils/api';

const CertificateModal = ({ isOpen, onClose, deviceId, deviceName, initialCertText }) => {
  const [copied, setCopied] = useState(false);
  const [selectedType, setSelectedType] = useState('device_cert');
  const [certText, setCertText] = useState(initialCertText || '');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const certTypes = [
    { value: 'device_cert', label: 'Device Certificate (.crt)' },
    { value: 'ca_cert', label: 'CA Certificate (.crt)' },
    { value: 'private_key', label: 'Private Key (.key)' },
    { value: 'bundle', label: 'Certificate Bundle (.bundle.crt)' }
  ];

  useEffect(() => {
    if (isOpen && deviceId && selectedType !== 'device_cert') {
      loadCertificate();
    } else if (isOpen && selectedType === 'device_cert') {
      setCertText(initialCertText || '');
    }
  }, [isOpen, deviceId, selectedType, initialCertText]);

  const loadCertificate = async () => {
    if (!deviceId) return;
    
    setLoading(true);
    setError('');
    
    try {
      const response = await devicesAPI.view(deviceId, selectedType);
      setCertText(response.data.cert_text);
    } catch (err) {
      setError('Failed to load certificate');
      console.error('Error loading certificate:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleTypeChange = (newType) => {
    setSelectedType(newType);
    setCopied(false);
  };

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(certText);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy text: ', err);
    }
  };

  return (
    <Transition appear show={isOpen} as={Fragment}>
      <Dialog as="div" className="relative z-10" onClose={onClose}>
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-black bg-opacity-25" />
        </Transition.Child>

        <div className="fixed inset-0 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4 text-center">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 scale-95"
              enterTo="opacity-100 scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 scale-100"
              leaveTo="opacity-0 scale-95"
            >
              <Dialog.Panel className="w-full max-w-4xl transform overflow-hidden rounded-2xl bg-white p-6 text-left align-middle shadow-xl transition-all">
                <div className="flex items-center justify-between mb-4">
                  <Dialog.Title
                    as="h3"
                    className="text-lg font-medium leading-6 text-gray-900"
                  >
                    Certificate for {deviceName}
                  </Dialog.Title>
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={handleCopy}
                      className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                    >
                      {copied ? (
                        <>
                          <CheckIcon className="h-4 w-4 mr-2 text-green-500" />
                          Copied!
                        </>
                      ) : (
                        <>
                          <ClipboardDocumentIcon className="h-4 w-4 mr-2" />
                          Copy
                        </>
                      )}
                    </button>
                    <button
                      onClick={onClose}
                      className="rounded-md bg-white text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
                    >
                      <span className="sr-only">Close</span>
                      <XMarkIcon className="h-6 w-6" aria-hidden="true" />
                    </button>
                  </div>
                </div>

                {/* Certificate Type Selector */}
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Certificate Type
                  </label>
                  <select
                    value={selectedType}
                    onChange={(e) => handleTypeChange(e.target.value)}
                    className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                  >
                    {certTypes.map((type) => (
                      <option key={type.value} value={type.value}>
                        {type.label}
                      </option>
                    ))}
                  </select>
                </div>

                {error && (
                  <div className="mb-4 rounded-md bg-red-50 p-4">
                    <div className="text-sm text-red-700">{error}</div>
                  </div>
                )}

                <div className="mt-4">
                  <div className="bg-gray-50 rounded-lg p-4 border">
                    {loading ? (
                      <div className="flex items-center justify-center h-32">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
                        <span className="ml-2 text-gray-600">Loading certificate...</span>
                      </div>
                    ) : (
                      <pre className="text-sm text-gray-900 whitespace-pre-wrap break-all max-h-96 overflow-y-auto">
                        {certText}
                      </pre>
                    )}
                  </div>
                </div>

                <div className="mt-6 flex justify-end">
                  <button
                    type="button"
                    className="inline-flex justify-center rounded-md border border-transparent bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
                    onClick={onClose}
                  >
                    Close
                  </button>
                </div>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition>
  );
};

export default CertificateModal;
