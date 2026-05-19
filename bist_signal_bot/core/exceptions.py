from typing import Any


class BistSignalBotError(Exception):
    """Base exception class for BIST Signal Bot."""
    def __init__(self, message: str, error_code: str | None = None, context: dict[str, Any] | None = None, recoverable: bool = True):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.context = context or {}
        self.recoverable = recoverable

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

class BistBotError(Exception): pass

class RuntimeErrorBase(BistBotError): pass
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
