import React from 'react';
import { S3PageHeader } from '@smart3ai/design-system';

const CrudPageHeader = ({ title, subtitle, actionLabel, onAction, actionDisabled = false }) => {
  return (
    <S3PageHeader
      title={title}
      subtitle={subtitle}
      actionLabel={actionLabel}
      onAction={onAction}
      actionDisabled={actionDisabled}
    />
  );
};

export default CrudPageHeader;
