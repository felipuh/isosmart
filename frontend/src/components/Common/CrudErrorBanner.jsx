import React from 'react';
import { S3Banner } from '@smart3ai/design-system';
import { useI18n } from '../../context/I18nContext';

const CrudErrorBanner = ({ message, onClose }) => {
  const { t } = useI18n();

  if (!message) return null;

  return (
    <S3Banner
      description={message}
      dismissLabel={t('common.buttons.dismissError')}
      onDismiss={onClose}
      tone="danger"
    />
  );
};

export default CrudErrorBanner;
