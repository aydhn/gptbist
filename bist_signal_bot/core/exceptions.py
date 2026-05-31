class BISTBotError(Exception):
    pass

from typing import Any


class BistSignalBotError(Exception):
    """Base exception class for BIST Signal Bot."""
    def __init__(self, message: str, error_code: str | None = None, context: dict[str, Any] | None = None, recoverable: bool = True):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.context = context or {}
        self.recoverable = recoverable


class QAError(BistSignalBotError):
    pass

class QAFixtureError(QAError):
    pass

class SyntheticDataError(QAError):
    pass

class QAScenarioError(QAError):
    pass

class ScenarioReplayError(QAError):
    pass

class SmokeTestError(QAError):
    pass

class RegressionMatrixError(QAError):
    pass

class ReleaseGateError(QAError):
    pass

class ReproducibilityError(QAError):
    pass

class QASafetyCheckError(QAError):
    pass

class NoExternalCallError(QAError):
    pass

class QACoverageMatrixError(QAError):
    pass

class QAStorageError(QAError):
    pass

class ConfigurationError(BistSignalBotError):
    """Raised when there is a configuration issue."""
    pass

class DataProviderError(BistSignalBotError):
    """Raised when a data provider fails to fetch data."""
    pass


class InvalidSymbolError(BistSignalBotError):
    """Raised when a symbol is invalid or doesn't match internal format rules."""
    pass

class SymbolUniverseError(BistSignalBotError):
    """Raised for general SymbolUniverse related errors."""
    pass

class DuplicateSymbolError(SymbolUniverseError):
    """Raised when attempting to add a duplicate symbol to the universe."""
    pass

class DataProviderTimeoutError(DataProviderError):
    """Raised when a data provider request times out."""
    pass

class DataProviderValidationError(DataProviderError):
    """Raised when fetched data is invalid or missing required columns."""
    pass

class StorageError(BistSignalBotError):
    """Raised when there is a general storage error."""
    pass

class MarketDataStoreError(StorageError):
    """Raised when there is an error specific to the local market data store."""
    pass

class DataQualityError(BistSignalBotError):
    """Raised when data quality checks fail and fail_on_error is configured."""
    pass

class MarketCalendarError(BistSignalBotError):
    """Raised when there is an error in market calendar calculations."""
    pass

class MarketSessionError(BistSignalBotError):
    """Raised when there is an error in market session logic."""
    pass

class NotificationError(BistSignalBotError):
    """Raised when there is an error in the notification system."""
    pass

class TelegramConfigurationError(NotificationError):
    """Raised when there is an error with Telegram configuration."""
    pass

class TelegramSendError(NotificationError):
    """Raised when there is an error sending a Telegram message."""
    pass

class AuditLogError(BistSignalBotError):
    """Raised when there is an error writing an audit log."""
    pass

class OperationalSafetyError(BistSignalBotError):
    """Raised when an operational safety check fails."""
    pass

class UniverseStoreError(BistSignalBotError):
    """Raised when there is an error interacting with the Universe Store."""
    pass

class UniverseImportError(BistSignalBotError):
    """Raised when there is an error importing a universe file."""
    pass

class UniverseValidationError(BistSignalBotError):
    """Raised when a symbol universe is invalid."""
    pass

class DataNormalizationError(BistSignalBotError):
    """Raised when there is an error normalizing data schema or formats."""
    pass

class DataCleaningError(BistSignalBotError):
    """Exception raised for errors during data cleaning."""
    pass

class CorporateActionError(BistSignalBotError):
    """Raised when there is an error processing corporate actions."""
    pass

class CorporateActionStoreError(StorageError):
    """Raised when there is an error interacting with the corporate action store."""
    pass

class PriceAdjustmentError(BistSignalBotError):
    """Raised when an error occurs during price adjustment logic."""
    pass

class IndicatorError(BistSignalBotError):
    """Base exception for indicator errors."""
    pass

class IndicatorValidationError(IndicatorError):
    """Raised when an indicator's inputs or parameters are invalid."""
    pass

class IndicatorCalculationError(IndicatorError):
    """Raised when an error occurs during indicator calculation."""
    pass

class IndicatorRegistryError(IndicatorError):
    """Raised when there is an error in the indicator registry."""
    pass

class PatternDetectionError(BistSignalBotError):
    """Raised when an error occurs during pattern detection."""
    pass

class PatternValidationError(PatternDetectionError):
    """Raised when pattern inputs or parameters are invalid."""
    pass

class PatternEngineError(PatternDetectionError):
    """Raised when there is an error in the pattern engine."""
    pass

class PatternDetectionError(BistSignalBotError):
    """Raised when an error occurs during pattern detection."""
    pass

class PatternValidationError(PatternDetectionError):
    """Raised when pattern inputs or parameters are invalid."""
    pass

class PatternEngineError(PatternDetectionError):
    """Raised when there is an error in the pattern engine."""
    pass

class DivergenceError(BistSignalBotError):
    """Raised when an error occurs during divergence detection."""
    pass

class DivergenceValidationError(DivergenceError):
    """Raised when divergence inputs or parameters are invalid."""
    pass

class DivergenceDetectionError(DivergenceError):
    """Raised when there is an error detecting divergences."""
    pass

class PivotDetectionError(DivergenceError):
    """Raised when there is an error detecting pivot points."""
    pass

class TimeframeError(BistSignalBotError):
    """Base exception for timeframe errors."""
    pass

class TimeframeResampleError(TimeframeError):
    """Raised when an error occurs during timeframe resampling."""
    pass

class TimeframeAlignmentError(TimeframeError):
    """Raised when an error occurs during timeframe alignment."""
    pass

class MultiTimeframeError(TimeframeError):
    """Raised when an error occurs in the multi-timeframe engine or feature builder."""
    pass

class StrategyError(BistSignalBotError):
    """Raised when a strategy execution fails."""
    pass

class StrategyValidationError(StrategyError):
    """Raised when a strategy configuration or context is invalid."""
    pass

class StrategyExecutionError(StrategyError):
    """Raised when a strategy encounters an error during run."""
    pass

class StrategyRegistryError(StrategyError):
    """Raised when there is an error in the strategy registry."""
    pass

class SignalCandidateError(BistSignalBotError):
    """Raised when a signal candidate is invalid."""
    pass

class BenchmarkError(BistSignalBotError):
    """Base exception for benchmark errors."""
    pass

class BenchmarkValidationError(BenchmarkError):
    """Raised when benchmark parameters or inputs are invalid."""
    pass

class BenchmarkExecutionError(BenchmarkError):
    """Raised when a benchmark encounters an error during run."""
    pass

class BenchmarkRegistryError(BenchmarkError):
    """Raised when there is an error in the benchmark registry."""
    pass

class CostModelError(BistSignalBotError):
    """Base exception for cost model errors."""
    pass

class CommissionModelError(CostModelError):
    """Raised when there is an error in commission calculation."""
    pass

class SlippageModelError(CostModelError):
    """Raised when there is an error in slippage calculation."""
    pass

class SpreadModelError(CostModelError):
    """Raised when there is an error in spread calculation."""
    pass

class TransactionCostError(CostModelError):
    """Raised when there is an error in overall transaction cost calculation."""
    pass

class BacktestError(BistSignalBotError):
    pass

class PortfolioAccountingError(BacktestError):
    pass

class BacktestExecutionError(BacktestError):
    pass

class BacktestValidationError(BacktestError):
    pass

class BacktestMetricsError(BistSignalBotError):
    pass

class BacktestReportError(BistSignalBotError):
    pass

class BenchmarkComparisonError(BistSignalBotError):
    pass

class PerformanceAnalysisError(BistSignalBotError):
    pass


class ValidationAnalysisError(BistSignalBotError):
    pass

class TimeSeriesSplitError(ValidationAnalysisError):
    pass

class WalkForwardError(ValidationAnalysisError):
    pass

class RobustnessAnalysisError(ValidationAnalysisError):
    pass

class OverfitRiskError(ValidationAnalysisError):
    pass

class RiskEngineError(BistSignalBotError):
    pass

class RiskValidationError(RiskEngineError):
    pass

class PositionSizingError(RiskEngineError):
    pass

class StopModelError(RiskEngineError):
    pass

class TargetModelError(RiskEngineError):
    pass

class RiskFilterError(RiskEngineError):
    pass

class RiskDecisionError(RiskEngineError):
    pass

class PortfolioError(BistSignalBotError):
    pass

class PortfolioValidationError(PortfolioError):
    pass

class PortfolioRiskError(PortfolioError):
    pass

class PortfolioAllocationError(PortfolioError):
    pass

class CorrelationAnalysisError(PortfolioError):
    pass

class ExposureLimitError(PortfolioError):
    pass

class PaperTradingError(BistSignalBotError):
    """Base exception for Paper Trading Engine errors."""
    pass

class PaperAccountError(PaperTradingError):
    """Raised when an error occurs with a paper account."""
    pass

class PaperLedgerError(PaperTradingError):
    """Raised when an error occurs reading or writing the paper ledger."""
    pass

class PaperOrderError(PaperTradingError):
    """Raised when a paper order is invalid or cannot be processed."""
    pass

class PaperExecutionError(PaperTradingError):
    """Raised when an error occurs simulating paper order execution."""
    pass

class PaperPositionError(PaperTradingError):
    """Raised when an error occurs managing paper positions."""
    pass

class ScannerError(BistSignalBotError):
    pass

class ScannerValidationError(ScannerError):
    pass

class ScannerExecutionError(ScannerError):
    pass

class ScannerRankingError(ScannerError):
    pass

class ScannerStorageError(ScannerError):
    pass

class ScannerReportError(ScannerError):
    pass

class OptimizationError(BistSignalBotError):
    pass

class OptimizationValidationError(OptimizationError):
    pass

class SearchSpaceError(OptimizationError):
    pass

class ObjectiveFunctionError(OptimizationError):
    pass

class GridSearchError(OptimizationError):
    pass

class RandomSearchError(OptimizationError):
    pass

class WalkForwardOptimizationError(OptimizationError):
    pass

class OptimizationReportError(OptimizationError):
    pass

class OptimizationStorageError(OptimizationError):
    pass

class MLDataError(BistSignalBotError):
    pass

class MLDatasetError(BistSignalBotError):
    pass

class MLLabelError(BistSignalBotError):
    pass

class MLFeatureStoreError(BistSignalBotError):
    pass

class MLPreprocessingError(BistSignalBotError):
    pass

class MLLeakageError(BistSignalBotError):
    pass

class MLSchemaError(BistSignalBotError):
    pass


class MLTrainingError(BistSignalBotError):
    pass

class MLTrainingValidationError(MLTrainingError):
    pass

class MLEstimatorError(MLTrainingError):
    pass

class MLEvaluationError(MLTrainingError):
    pass

class MLPredictionError(MLTrainingError):
    pass

class MLModelRegistryError(MLTrainingError):
    pass

class MLModelStorageError(MLTrainingError):
    pass

class MLInferenceError(BistSignalBotError):
    pass

class MLFeatureAlignmentError(MLInferenceError):
    pass

class MLFilterError(MLInferenceError):
    pass

class MLScoreError(MLInferenceError):
    pass

class MLSignalIntegrationError(MLInferenceError):
    pass

class MLModelMismatchError(MLInferenceError):
    pass

class RegimeError(BistSignalBotError):
    pass
class RegimeValidationError(RegimeError):
    pass
class RegimeFeatureError(RegimeError):
    pass
class RegimeClassificationError(RegimeError):
    pass
class RegimeFilterError(RegimeError):
    pass
class RegimeUniverseError(RegimeError):
    pass




class PerformanceError(BistSignalBotError):
    pass

class PerformanceValidationError(PerformanceError):
    pass

class ProfilingError(PerformanceError):
    pass

class ResourceMonitorError(PerformanceError):
    pass

class CacheOptimizationError(PerformanceError):
    pass

class BatchTuningError(PerformanceError):
    pass

class PerformanceBenchmarkError(PerformanceError):
    pass

class PerformanceStorageError(PerformanceError):
    pass

class BistSignalBotError(Exception): pass

class RuntimeErrorBase(BistSignalBotError): pass
class RuntimeValidationError(RuntimeErrorBase): pass
class RuntimeLockError(RuntimeErrorBase): pass
class RuntimeStateError(RuntimeErrorBase): pass
class RuntimeJobError(RuntimeErrorBase): pass
class RuntimeSchedulerError(RuntimeErrorBase): pass
class RuntimePipelineError(RuntimeErrorBase): pass
class RuntimeStorageError(RuntimeErrorBase): pass
class RuntimeNotificationError(RuntimeErrorBase): pass

class MonitoringError(BistSignalBotError):
    pass

class MonitoringValidationError(MonitoringError):
    pass

class HeartbeatError(MonitoringError):
    pass

class MetricsError(MonitoringError):
    pass

class AlertError(MonitoringError):
    pass

class DiagnosticsError(MonitoringError):
    pass

class SelfHealingError(MonitoringError):
    pass

class MonitoringStorageError(MonitoringError):
    pass

class SecurityError(BistSignalBotError):
    pass
class SecretLeakError(SecurityError):
    pass
class ForbiddenActionError(SecurityError):
    pass
class UnsafeClaimError(SecurityError):
    pass
class PathSecurityError(SecurityError):
    pass
class KillSwitchActiveError(SecurityError):
    pass
class SecurityPreflightError(SecurityError):
    pass
class ConfigSecurityError(SecurityError):
    pass

class QualityError(BistSignalBotError):
    pass

class QualityValidationError(QualityError):
    pass

class QualityToolError(QualityError):
    pass

class QualityGateError(QualityError):
    pass

class QualityTestRunnerError(QualityError):
    pass

class QualityCoverageError(QualityError):
    pass

class QualityRegressionError(QualityError):
    pass

class QualityStorageError(QualityError):
    pass


class PackagingError(BistSignalBotError):
    pass

class EnvironmentDoctorError(PackagingError):
    pass

class DependencyCheckError(PackagingError):
    pass

class InstallerGenerationError(PackagingError):
    pass

class ReleaseBundleError(PackagingError):
    pass

class ManifestError(PackagingError):
    pass

class PackagingStorageError(PackagingError):
    pass

class DocsError(BistSignalBotError):
    pass

class DocsValidationError(DocsError):
    pass

class DocsGenerationError(DocsError):
    pass

class DocsCatalogError(DocsError):
    pass

class DocsRunbookError(DocsError):
    pass

class DocsExampleError(DocsError):
    pass

class DocsStorageError(DocsError):
    pass
class AdaptiveError(BistSignalBotError):
    pass

class AdaptiveValidationError(AdaptiveError):
    pass

class AdaptivePolicyError(AdaptiveError):
    pass

class AdaptiveEvidenceError(AdaptiveError):
    pass

class AdaptiveScoringError(AdaptiveError):
    pass

class AdaptiveSelectionError(AdaptiveError):
    pass

class AdaptiveParameterStoreError(AdaptiveError):
    pass

class AdaptiveRefreshError(AdaptiveError):
    pass

class AdaptiveStorageError(AdaptiveError):
    pass

class ResearchError(BistSignalBotError):
    pass

class ResearchValidationError(ResearchError):
    pass

class ResearchLedgerError(ResearchError):
    pass

class ResearchEventError(ResearchError):
    pass

class ResearchLineageError(ResearchError):
    pass

class SignalJournalError(ResearchError):
    pass

class ResearchComparisonError(ResearchError):
    pass

class ResearchAttributionError(ResearchError):
    pass

class ResearchNoteError(ResearchError):
    pass

class ResearchQueryError(ResearchError):
    pass

class ResearchStorageError(ResearchError):
    pass

class ReportError(BistSignalBotError):
    pass

class ReportValidationError(ReportError):
    pass

class ReportCollectionError(ReportError):
    pass

class ReportTemplateError(ReportError):
    pass

class ReportGenerationError(ReportError):
    pass

class ReportExportError(ReportError):
    pass

class ReportDigestError(ReportError):
    pass

class ReportStorageError(ReportError):
    pass

class ScenarioError(BistSignalBotError):
    pass

class ScenarioValidationError(ScenarioError):
    pass

class ScenarioFixtureError(ScenarioError):
    pass

class ScenarioStepError(ScenarioError):
    pass

class ScenarioRunnerError(ScenarioError):
    pass

class GoldenRegressionError(ScenarioError):
    pass

class ScenarioStorageError(ScenarioError):
    pass


class ReleaseError(BistSignalBotError):
    """Base exception for Release Manager errors."""
    pass

class ReleaseValidationError(ReleaseError):
    """Raised when release configuration or model validation fails."""
    pass

class ReleaseCheckError(ReleaseError):
    """Raised when a release check fails to execute properly."""
    pass

class ReleaseReadinessError(ReleaseError):
    """Raised when release readiness evaluation fails."""
    pass

class ReleaseRehearsalError(ReleaseError):
    """Raised when safe launch rehearsal fails."""
    pass

class ReleaseCandidateError(ReleaseError):
    """Raised when release candidate building fails."""
    pass

class ReleaseNotesError(ReleaseError):
    """Raised when release notes generation fails."""
    pass

class ReleaseStorageError(ReleaseError):
    """Raised when storing release artifacts fails."""
    pass

class DataProviderV2Error(BistSignalBotError):
    pass

class DataImportError(BistSignalBotError):
    pass

class DataLineageError(BistSignalBotError):
    pass

class DataFreshnessError(BistSignalBotError):
    pass

class IncrementalUpdateError(BistSignalBotError):
    pass

class ProviderFallbackError(BistSignalBotError):
    pass

class ProviderHealthError(BistSignalBotError):
    pass

class DataComparisonError(BistSignalBotError):
    pass


class FundamentalError(BistSignalBotError): pass
class FundamentalValidationError(FundamentalError): pass
class FundamentalImportError(FundamentalError): pass
class FundamentalStorageError(FundamentalError): pass
class FundamentalRatioError(FundamentalError): pass
class FundamentalFactorError(FundamentalError): pass
class CorporateEventError(FundamentalError): pass
class FundamentalFilterError(FundamentalError): pass
class FundamentalLookaheadError(FundamentalError): pass

class BreadthError(BistSignalBotError):
    pass

class BreadthValidationError(BreadthError):
    pass

class BreadthCalculationError(BreadthError):
    pass

class RelativeStrengthError(BreadthError):
    pass

class SectorRotationError(BreadthError):
    pass

class CrossSectionalRankingError(BreadthError):
    pass

class BreadthRegimeError(BreadthError):
    pass

class BreadthStorageError(BreadthError):
    pass

class BreadthLookaheadError(BreadthError):
    pass


class EnsembleError(BistSignalBotError):
    pass

class EnsembleValidationError(EnsembleError):
    pass

class EnsembleWeightError(EnsembleError):
    pass

class EnsembleCollectionError(EnsembleError):
    pass

class EnsembleScoringError(EnsembleError):
    pass

class EnsembleConflictError(EnsembleError):
    pass

class EnsembleExplainabilityError(EnsembleError):
    pass

class EnsembleStorageError(EnsembleError):
    pass

class EnsembleLookaheadError(EnsembleError):
    pass

class PortfolioResearchError(BistSignalBotError):
    pass

class PortfolioResearchValidationError(PortfolioResearchError):
    pass

class PortfolioAllocationError(PortfolioResearchError):
    pass

class PortfolioConstraintError(PortfolioResearchError):
    pass

class PortfolioExposureError(PortfolioResearchError):
    pass

class PortfolioCorrelationError(PortfolioResearchError):
    pass

class PortfolioRebalanceError(PortfolioResearchError):
    pass

class BasketSimulationError(PortfolioResearchError):
    pass

class PortfolioResearchStorageError(PortfolioResearchError):
    pass

class StressTestError(BistSignalBotError):
    pass

class StressValidationError(StressTestError):
    pass

class MonteCarloError(StressTestError):
    pass

class ShockScenarioError(StressTestError):
    pass

class DrawdownSimulationError(StressTestError):
    pass

class RiskOfRuinError(StressTestError):
    pass

class StressStorageError(StressTestError):
    pass

class DriftError(BistSignalBotError):
    pass

class DriftValidationError(DriftError):
    pass

class FeatureDriftError(DriftError):
    pass

class ModelDriftError(DriftError):
    pass

class CalibrationError(DriftError):
    pass

class SignalDecayError(DriftError):
    pass

class StrategyDecayError(DriftError):
    pass

class PortfolioDriftError(DriftError):
    pass

class DriftReferenceError(DriftError):
    pass

class DriftStorageError(DriftError):
    pass

class ResearchLabError(BistSignalBotError):
    pass

class ResearchLabValidationError(ResearchLabError):
    pass

class ResearchJobPlanningError(ResearchLabError):
    pass

class ResearchQueueError(ResearchLabError):
    pass

class ResearchJobExecutionError(ResearchLabError):
    pass

class ResearchJobDependencyError(ResearchLabError):
    pass

class ResearchJobBudgetError(ResearchLabError):
    pass

class ResearchJobRetryError(ResearchLabError):
    pass

class ResearchLabStorageError(ResearchLabError):
    pass

class MaintenanceError(BistSignalBotError):
    pass

class BackupError(MaintenanceError):
    pass

class BackupValidationError(BackupError):
    pass

class RestoreError(MaintenanceError):
    pass

class RestoreValidationError(RestoreError):
    pass

class RetentionError(MaintenanceError):
    pass

class CleanupError(MaintenanceError):
    pass

class MigrationError(MaintenanceError):
    pass

class MaintenanceDoctorError(MaintenanceError):
    pass

class BackupManifestError(MaintenanceError):
    pass

class ChecksumError(MaintenanceError):
    pass

class GovernanceError(BistSignalBotError):
    pass

class GovernancePolicyError(GovernanceError):
    pass

class GovernanceRuleError(GovernanceError):
    pass

class AuditReviewError(GovernanceError):
    pass

class EvidencePackError(GovernanceError):
    pass

class GovernanceGateError(GovernanceError):
    pass

class AttestationError(GovernanceError):
    pass

class GovernanceStorageError(GovernanceError):
    pass


class ReviewError(BistSignalBotError):
    pass

class ReviewValidationError(ReviewError):
    pass

class ReviewInboxError(ReviewError):
    pass

class ReviewChecklistError(ReviewError):
    pass

class ReviewThesisError(ReviewError):
    pass

class ReviewDecisionError(ReviewError):
    pass

class ReviewJournalError(ReviewError):
    pass

class ReviewFollowupError(ReviewError):
    pass

class ReviewStorageError(ReviewError):
    pass


class KnowledgeBaseError(BistSignalBotError):
    """Base exception for Knowledge Base operations."""
    pass


class KnowledgeValidationError(KnowledgeBaseError):
    """Raised when knowledge document or configuration validation fails."""
    pass


class KnowledgeSourceError(KnowledgeBaseError):
    """Raised when knowledge sources cannot be collected or accessed."""
    pass


class KnowledgeIndexError(KnowledgeBaseError):
    """Raised when knowledge indexing fails."""
    pass


class KnowledgeSearchError(KnowledgeBaseError):
    """Raised when knowledge search execution fails."""
    pass


class KnowledgeEmbeddingError(KnowledgeBaseError):
    """Raised when local embedding generation or fallback fails."""
    pass


class KnowledgeRetrievalError(KnowledgeBaseError):
    """Raised when evidence retrieval fails."""
    pass


class CaseLibraryError(KnowledgeBaseError):
    """Raised when similar case library operations fail."""
    pass


class AnalystMemoryError(KnowledgeBaseError):
    """Raised when analyst memory card generation fails."""
    pass


class KnowledgeStorageError(KnowledgeBaseError):
    """Raised when knowledge storage read/write fails."""
    pass


class TelegramCenterError(BistSignalBotError):
    """Base error for Telegram Center operations."""
    pass

class TelegramConfigError(TelegramCenterError):
    """Error related to Telegram Center configuration."""
    pass

class TelegramPermissionError(TelegramCenterError):
    """Error related to unauthorized access or missing permissions."""
    pass

class TelegramCommandParseError(TelegramCenterError):
    """Error parsing a Telegram command."""
    pass

class TelegramCommandSafetyError(TelegramCenterError):
    """Error related to command safety guards and forbidden actions."""
    pass

class TelegramRoutingError(TelegramCenterError):
    """Error routing a Telegram command."""
    pass

class TelegramClientError(TelegramCenterError):
    """Error communicating with the Telegram API."""
    pass

class NotificationInboxError(TelegramCenterError):
    """Error related to the notification inbox."""
    pass

class DigestOrchestrationError(TelegramCenterError):
    """Error orchestrating a digest report."""
    pass

class TelegramRateLimitError(TelegramCenterError):
    """Error related to Telegram rate limiting."""
    pass

class TelegramStorageError(TelegramCenterError):
    """Error related to Telegram Center storage."""
    pass

class SchedulerError(BISTBotError):
    pass

class ScheduleValidationError(SchedulerError):
    pass

class MarketCalendarError(SchedulerError):
    pass

class MarketSessionError(SchedulerError):
    pass

class ScheduleTriggerError(SchedulerError):
    pass

class DueJobError(SchedulerError):
    pass

class SchedulerLockError(SchedulerError):
    pass

class ScheduledJobExecutionError(SchedulerError):
    pass

class SchedulerStorageError(SchedulerError):
    pass

class DeploymentError(BistSignalBotError):
    """Base exception for Deployment operations."""
    pass

class DeploymentValidationError(DeploymentError):
    """Raised when deployment configuration or model validation fails."""
    pass

class DeploymentProfileError(DeploymentError):
    """Raised when a deployment profile is invalid or unsafe."""
    pass

class EnvironmentDoctorError(DeploymentError):
    """Raised when environment validation fails."""
    pass

class FirstRunError(DeploymentError):
    """Raised when first run wizard encounters an error."""
    pass

class EnvTemplateError(DeploymentError):
    """Raised when environment template generation fails."""
    pass

class DeploymentDirectoryError(DeploymentError):
    """Raised when deployment directory initialization fails."""
    pass

class DeploymentSmokeTestError(DeploymentError):
    """Raised when deployment smoke tests fail."""
    pass

class OperatorRunbookError(DeploymentError):
    """Raised when operator runbook generation fails."""
    pass

class DeploymentStorageError(DeploymentError):
    """Raised when deployment storage read/write fails."""
    pass

class PerformanceError(BistSignalBotError):
    pass

class PerformanceValidationError(PerformanceError):
    pass

class ProfilerError(PerformanceError):
    pass

class BenchmarkError(PerformanceError):
    pass

class ResourceSamplingError(PerformanceError):
    pass

class PerformanceBaselineError(PerformanceError):
    pass

class PerformanceRegressionError(PerformanceError):
    pass

class BottleneckAnalysisError(PerformanceError):
    pass

class PerformanceStorageError(PerformanceError):
    pass

class PerformanceError(BistSignalBotError):
    """Base exception for performance profiling and benchmarking."""
    pass

class PerformanceValidationError(PerformanceError):
    """Raised when benchmark or profile validation fails."""
    pass

class ProfilerError(PerformanceError):
    """Raised when there is an error during profiling."""
    pass

class BenchmarkError(PerformanceError):
    """Raised when there is an error running a benchmark."""
    pass

class ResourceSamplingError(PerformanceError):
    """Raised when there is an error sampling system resources."""
    pass

class PerformanceBaselineError(PerformanceError):
    """Raised when there is an error managing performance baselines."""
    pass

class PerformanceRegressionError(PerformanceError):
    """Raised when there is an error during regression checking."""
    pass

class BottleneckAnalysisError(PerformanceError):
    """Raised when bottleneck analysis fails."""
    pass

class PerformanceStorageError(PerformanceError):
    """Raised when saving or loading performance data fails."""
    pass

class ConfigRegistryError(BistSignalBotError):
    """Base exception for Config Registry operations."""
    pass

class ConfigSchemaError(ConfigRegistryError):
    pass

class FeatureFlagError(ConfigRegistryError):
    pass

class RuntimeProfileError(ConfigRegistryError):
    pass

class ConfigValidationError(ConfigRegistryError):
    pass

class ConfigSnapshotError(ConfigRegistryError):
    pass

class ConfigDiffError(ConfigRegistryError):
    pass

class ConfigDriftError(ConfigRegistryError):
    pass

class ConfigGateError(ConfigRegistryError):
    pass

class ConfigRegistryStorageError(ConfigRegistryError):
    pass

class InstrumentError(BistSignalBotError):
    pass

class InstrumentValidationError(InstrumentError):
    pass

class InstrumentMasterError(InstrumentError):
    pass

class SymbolLifecycleError(InstrumentError):
    pass

class UniverseBuilderError(InstrumentError):
    pass

class CorporateActionError(BistSignalBotError):
    pass

class CorporateActionImportError(CorporateActionError):
    pass

class CorporateActionValidationError(CorporateActionError):
    pass

class PriceAdjustmentError(CorporateActionError):
    pass

class DataReconciliationError(BistSignalBotError):
    pass

class AdjustedPriceError(DataReconciliationError):
    pass

class ValidationError(BistSignalBotError):
    pass

class StrategyValidationError(ValidationError):
    pass

class WalkForwardError(ValidationError):
    pass

class PurgedCVError(ValidationError):
    pass

class ParameterStabilityError(ValidationError):
    pass

class OverfitDiagnosticsError(ValidationError):
    pass

class RegimeRobustnessError(ValidationError):
    pass

class CostRobustnessError(ValidationError):
    pass

class ValidationStorageError(ValidationError):
    pass

class MonteCarloError(BistSignalBotError):
    pass

class MonteCarloValidationError(MonteCarloError):
    pass

class ResamplingError(MonteCarloError):
    pass

class BootstrapError(MonteCarloError):
    pass

class PathSimulationError(MonteCarloError):
    pass

class TradeSimulationError(MonteCarloError):
    pass

class CostRandomizationError(MonteCarloError):
    pass

class RealityCheckError(MonteCarloError):
    pass

class MonteCarloStorageError(MonteCarloError):
    pass


class StrategyRegistryError(BistSignalBotError):
    pass

class StrategyCatalogError(StrategyRegistryError):
    pass

class StrategyScorecardError(StrategyRegistryError):
    pass

class StrategyEvidenceError(StrategyRegistryError):
    pass

class StrategyLifecycleError(StrategyRegistryError):
    pass

class StrategyPromotionError(StrategyRegistryError):
    pass

class StrategyGateError(StrategyRegistryError):
    pass

class StrategyRegistryStorageError(StrategyRegistryError):
    pass


class ExplainabilityError(BistSignalBotError):
    pass

class FeatureAttributionError(ExplainabilityError):
    pass

class IndicatorStateError(ExplainabilityError):
    pass

class RuleTraceError(ExplainabilityError):
    pass

class MLExplainabilityError(ExplainabilityError):
    pass

class EnsembleExplainabilityError(ExplainabilityError):
    pass

class EvidenceCardError(ExplainabilityError):
    pass

class DecisionTraceError(ExplainabilityError):
    pass

class ExplainabilityStorageError(ExplainabilityError):
    pass

class CalibrationError(BistSignalBotError):
    pass

class CalibrationValidationError(CalibrationError):
    pass

class OutcomeDatasetError(CalibrationError):
    pass

class ReliabilityCurveError(CalibrationError):
    pass

class SignalCalibratorError(CalibrationError):
    pass

class ThresholdTuningError(CalibrationError):
    pass

class OutcomeCohortError(CalibrationError):
    pass

class ErrorTaxonomyError(CalibrationError):
    pass

class CalibrationStorageError(CalibrationError):
    pass

class PortfolioLedgerError(BistSignalBotError):
    pass

class PortfolioLedgerValidationError(PortfolioLedgerError):
    pass

class PortfolioLifecycleError(PortfolioLedgerError):
    pass

class PortfolioValuationError(PortfolioLedgerError):
    pass

class PortfolioAttributionError(PortfolioLedgerError):
    pass

class PortfolioOutcomeError(PortfolioLedgerError):
    pass

class RebalanceTrackingError(PortfolioLedgerError):
    pass

class PortfolioNavError(PortfolioLedgerError):
    pass

class PortfolioLedgerStorageError(PortfolioLedgerError):
    pass

class WhatIfError(BistSignalBotError):
    pass

class WhatIfValidationError(WhatIfError):
    pass

class ScenarioDefinitionError(WhatIfError):
    pass

class AssumptionOverrideError(WhatIfError):
    pass

class SensitivityAnalysisError(WhatIfError):
    pass

class CapitalScalingError(WhatIfError):
    pass

class PolicySandboxError(WhatIfError):
    pass

class CounterfactualAnalysisError(WhatIfError):
    pass

class WhatIfStorageError(WhatIfError):
    pass

class EventCalendarError(BistSignalBotError):
    pass

class EventValidationError(EventCalendarError):
    pass

class EventImportError(EventCalendarError):
    pass

class EventWindowError(EventCalendarError):
    pass

class EventRiskError(EventCalendarError):
    pass

class BlackoutPolicyError(EventCalendarError):
    pass

class EventLinkingError(EventCalendarError):
    pass

class EventStorageError(EventCalendarError):
    pass


class DisclosureError(BistSignalBotError):
    pass

class DisclosureImportError(DisclosureError):
    pass

class DisclosureValidationError(DisclosureError):
    pass

class DisclosureClassificationError(DisclosureError):
    pass

class DisclosureEntityLinkingError(DisclosureError):
    pass

class DisclosureRiskTagError(DisclosureError):
    pass

class DisclosureEventExtractionError(DisclosureError):
    pass

class DisclosureImpactError(DisclosureError):
    pass

class DisclosureDigestError(DisclosureError):
    pass

class DisclosureStorageError(DisclosureError):
    pass


class FinancialsError(BistSignalBotError):
    pass

class FinancialImportError(FinancialsError):
    pass

class FinancialValidationError(FinancialsError):
    pass

class FinancialNormalizationError(FinancialsError):
    pass

class FinancialPeriodError(FinancialsError):
    pass

class FinancialRatioError(FinancialsError):
    pass

class FinancialTrendError(FinancialsError):
    pass

class EarningsQualityError(FinancialsError):
    pass

class FinancialSectorCompareError(FinancialsError):
    pass

class FinancialStorageError(FinancialsError):
    pass

class ValuationError(BistSignalBotError):
    pass

class ValuationInputError(ValuationError):
    pass

class ValuationMultipleError(ValuationError):
    pass

class ValuationBandError(ValuationError):
    pass

class PeerValuationError(ValuationError):
    pass

class ValuationRiskError(ValuationError):
    pass

class ValuationScoringError(ValuationError):
    pass

class ValuationStorageError(ValuationError):
    pass


class FactorError(Exception): pass
class FactorInputError(FactorError): pass
class FactorScoringError(FactorError): pass
class FactorExposureError(FactorError): pass
class SectorRotationError(FactorError): pass
class ThemeExposureError(FactorError): pass
class FactorCrowdingError(FactorError): pass
class FactorAttributionError(FactorError): pass
class FactorStorageError(FactorError): pass

class BreadthError(BistSignalBotError):
    pass

class BreadthUniverseError(BreadthError):
    pass

class BreadthInputError(BreadthError):
    pass

class AdvanceDeclineError(BreadthError):
    pass

class ParticipationError(BreadthError):
    pass

class HighLowBreadthError(BreadthError):
    pass

class VolumeBreadthError(BreadthError):
    pass

class SectorBreadthError(BreadthError):
    pass

class BreadthDivergenceError(BreadthError):
    pass

class BreadthRegimeError(BreadthError):
    pass

class BreadthStorageError(BreadthError):
    pass

class ContextFusionError(BistSignalBotError):
    pass

class ContextSourceError(ContextFusionError):
    pass

class ContextCollectionError(ContextFusionError):
    pass

class ContextNormalizationError(ContextFusionError):
    pass

class ContextWeightingError(ContextFusionError):
    pass

class ContextConflictError(ContextFusionError):
    pass

class EvidenceGapError(ContextFusionError):
    pass

class ResearchGraphError(ContextFusionError):
    pass

class CompositeScoringError(ContextFusionError):
    pass

class ContextSnapshotError(ContextFusionError):
    pass

class ContextFusionStorageError(ContextFusionError):
    pass

class ReviewWorkflowError(BistSignalBotError):
    pass

class ReviewCaseError(ReviewWorkflowError):
    pass

class ReviewPlaybookError(ReviewWorkflowError):
    pass

class ReviewChecklistError(ReviewWorkflowError):
    pass

class ReviewPriorityError(ReviewWorkflowError):
    pass

class DecisionJournalError(ReviewWorkflowError):
    pass

class ReviewSignoffError(ReviewWorkflowError):
    pass

class ReviewDataActionError(ReviewWorkflowError):
    pass

class ReviewPatternError(ReviewWorkflowError):
    pass

class ReviewWorkflowStorageError(ReviewWorkflowError):
    pass


class OpsError(BistSignalBotError):
    pass
class OpsObservabilityError(OpsError):
    pass
class OpsStoreCheckError(OpsError):
    pass
class OpsStalenessError(OpsError):
    pass
class OpsIncidentError(OpsError):
    pass
class OpsRunbookError(OpsError):
    pass
class OpsBackupError(OpsError):
    pass
class OpsRestoreError(OpsError):
    pass
class OpsRetentionError(OpsError):
    pass
class OpsMigrationError(OpsError):
    pass
class OpsReadinessError(OpsError):
    pass
class OpsStorageError(OpsError):
    pass

class CLIUXError(BistSignalBotError):
    """Base exception for CLI UX operations."""
    pass

class CLIOutputContractError(CLIUXError):
    pass

class CLIOutputSchemaError(CLIUXError):
    pass

class CLIExitCodeError(CLIUXError):
    pass

class CLIUserFacingError(CLIUXError):
    pass

class CLIAliasError(CLIUXError):
    pass

class WorkflowRunnerError(CLIUXError):
    pass

class RecipeExecutorError(CLIUXError):
    pass

class CommandRegistryError(CLIUXError):
    pass

class CLICompatibilityError(CLIUXError):
    pass

class CLIUXStorageError(CLIUXError):
    pass

class DocsHubError(BISTBotError):
    """Base class for Docs Hub errors."""
    pass

class DocsIndexError(DocsHubError):
    pass

class DocsSearchError(DocsHubError):
    pass

class ArchitectureMapError(DocsHubError):
    pass

class CommandCookbookError(DocsHubError):
    pass

class TroubleshootingKBError(DocsHubError):
    pass

class DocsCoverageError(DocsHubError):
    pass

class MVPHandoffError(DocsHubError):
    pass

class DocsHubStorageError(DocsHubError):
    pass

class DataCatalogError(BistSignalBotError):
    pass

class DatasetContractError(DataCatalogError):
    pass

class DatasetRegistryError(DataCatalogError):
    pass

class DatasetProfilerError(DataCatalogError):
    pass

class DataQualityError(DataCatalogError):
    pass

class SchemaDriftError(DataCatalogError):
    pass

class DataLineageError(DataCatalogError):
    pass

class SourceProvenanceError(DataCatalogError):
    pass

class DataQualityGateError(DataCatalogError):
    pass

class DataCatalogStorageError(DataCatalogError):
    pass
class FeatureStoreError(BistSignalBotError):
    pass
class FeatureContractError(FeatureStoreError):
    pass
class FeatureRegistryError(FeatureStoreError):
    pass
class FeatureComputationError(FeatureStoreError):
    pass
class FeatureServingError(FeatureStoreError):
    pass
class FeatureQualityError(FeatureStoreError):
    pass
class FeatureDriftError(FeatureStoreError):
    pass
class FeatureLineageError(FeatureStoreError):
    pass
class FeatureLeakageError(FeatureStoreError):
    pass
class FeatureVersioningError(FeatureStoreError):
    pass
class FeatureStoreStorageError(FeatureStoreError):
    pass

class ModelRegistryError(BistSignalBotError):
    pass

class ModelExperimentError(ModelRegistryError):
    pass

class ModelArtifactError(ModelRegistryError):
    pass

class ModelCardError(ModelRegistryError):
    pass

class ModelValidationGovernanceError(ModelRegistryError):
    pass

class ModelCalibrationGovernanceError(ModelRegistryError):
    pass

class ModelPromotionError(ModelRegistryError):
    pass

class ModelDriftError(ModelRegistryError):
    pass

class ModelLineageError(ModelRegistryError):
    pass

class ModelGovernanceError(ModelRegistryError):
    pass

class ModelRegistryStorageError(ModelRegistryError):
    pass
