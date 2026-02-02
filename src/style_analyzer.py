"""
Style Analyzer - Analyzes and learns user writing styles.

This module provides functionality to analyze email writing patterns,
extract style characteristics, and build user profiles for personalized
email generation. It combines statistical analysis with AI-powered insights.
"""

import re
import json
import statistics
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pydantic import BaseModel, Field
import textstat
from rich.console import Console

console = Console()


@dataclass
class StyleMetrics:
    """Statistical metrics for writing style analysis."""
    formality_score: float  # 0-1, where 1 is very formal
    sentence_complexity: float  # 0-1, average sentence length normalized
    vocabulary_sophistication: float  # 0-1, based on word complexity
    sentiment_tendency: float  # -1 to 1 (negative to positive)
    directness_score: float  # 0-1, how direct the communication is
    avg_sentence_length: float
    avg_word_length: float
    exclamation_frequency: float
    question_frequency: float
    greeting_patterns: List[str]
    signature_patterns: List[str]
    common_phrases: List[str]


class UserProfile(BaseModel):
    """User writing style profile."""
    user_id: str
    email_address: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    # Style metrics
    style_metrics: StyleMetrics = Field(default_factory=lambda: StyleMetrics(
        formality_score=0.5,
        sentence_complexity=0.5,
        vocabulary_sophistication=0.5,
        sentiment_tendency=0.0,
        directness_score=0.5,
        avg_sentence_length=15.0,
        avg_word_length=4.5,
        exclamation_frequency=0.1,
        question_frequency=0.2,
        greeting_patterns=["Dear", "Hi", "Hello"],
        signature_patterns=["Best regards", "Sincerely", "Thanks"],
        common_phrases=[]
    ))
    
    # Preferences
    preferences: Dict[str, Any] = Field(default_factory=dict)
    
    # Learning data
    analyzed_emails: int = 0
    last_analysis: Optional[datetime] = None
    confidence_score: float = 0.0  # 0-1, how confident we are in the profile


class StyleAnalyzer:
    """Analyzes writing styles and builds user profiles."""
    
    def __init__(self, profile_dir: Optional[Path] = None):
        self.profile_dir = profile_dir or Path("profiles")
        self.profile_dir.mkdir(exist_ok=True)
        self.console = console
        
        # Sentiment words for basic sentiment analysis
        self.positive_words = {
            'great', 'excellent', 'wonderful', 'fantastic', 'amazing', 'good', 
            'love', 'like', 'happy', 'pleased', 'satisfied', 'delighted'
        }
        
        self.negative_words = {
            'bad', 'terrible', 'awful', 'horrible', 'hate', 'dislike', 
            'unhappy', 'disappointed', 'frustrated', 'angry', 'upset'
        }
        
        # Formal vs informal indicators
        self.formal_indicators = {
            'dear', 'sincerely', 'regards', 'respectfully', 'yours', 
            'cordially', 'formal', 'professional', 'appropriate'
        }
        
        self.informal_indicators = {
            'hey', 'hiya', 'sup', 'yo', 'cool', 'awesome', 'dude',
            'gonna', 'wanna', 'kinda', 'sorta', 'yeah', 'nah'
        }
    
    def analyze_email_content(self, email_text: str) -> StyleMetrics:
        """Analyze email content and extract style metrics."""
        if not email_text or not email_text.strip():
            raise ValueError("Email content is empty")
        
        # Clean and normalize text
        text = self._clean_text(email_text)
        sentences = self._split_sentences(text)
        words = self._tokenize(text)
        
        # Calculate metrics
        formality = self._calculate_formality(text, words)
        complexity = self._calculate_complexity(sentences, words)
        vocabulary = self._calculate_vocabulary_sophistication(words)
        sentiment = self._calculate_sentiment(words)
        directness = self._calculate_directness(text, sentences)
        
        # Basic statistics
        avg_sentence_length = statistics.mean([len(s.split()) for s in sentences]) if sentences else 0
        avg_word_length = statistics.mean([len(w) for w in words]) if words else 0
        exclamation_freq = text.count('!') / len(sentences) if sentences else 0
        question_freq = text.count('?') / len(sentences) if sentences else 0
        
        # Pattern extraction
        greeting_patterns = self._extract_greeting_patterns(email_text)
        signature_patterns = self._extract_signature_patterns(email_text)
        common_phrases = self._extract_common_phrases(email_text)
        
        return StyleMetrics(
            formality_score=formality,
            sentence_complexity=complexity,
            vocabulary_sophistication=vocabulary,
            sentiment_tendency=sentiment,
            directness_score=directness,
            avg_sentence_length=avg_sentence_length,
            avg_word_length=avg_word_length,
            exclamation_frequency=exclamation_freq,
            question_frequency=question_freq,
            greeting_patterns=greeting_patterns,
            signature_patterns=signature_patterns,
            common_phrases=common_phrases
        )
    
    def create_profile(self, user_id: str, email_address: str, 
                      initial_emails: Optional[List[str]] = None) -> UserProfile:
        """Create a new user profile."""
        profile = UserProfile(user_id=user_id, email_address=email_address)
        
        if initial_emails:
            profile = self.learn_from_emails(profile, initial_emails)
        
        self.save_profile(profile)
        return profile
    
    def learn_from_emails(self, profile: UserProfile, 
                          email_contents: List[str]) -> UserProfile:
        """Update profile by analyzing new emails."""
        if not email_contents:
            return profile
        
        # Analyze all emails
        all_metrics = []
        for email_content in email_contents:
            try:
                metrics = self.analyze_email_content(email_content)
                all_metrics.append(metrics)
            except Exception as e:
                self.console.print(f"[yellow]Warning: Failed to analyze email: {e}[/yellow]")
                continue
        
        if not all_metrics:
            return profile
        
        # Aggregate metrics with weighted average (giving more weight to recent emails)
        new_metrics = self._aggregate_metrics(all_metrics)
        
        # Update profile with learning rate
        learning_rate = 0.3  # How much to adjust based on new data
        current_metrics = profile.style_metrics
        
        profile.style_metrics = StyleMetrics(
            formality_score=self._weighted_average(
                current_metrics.formality_score, new_metrics.formality_score, learning_rate
            ),
            sentence_complexity=self._weighted_average(
                current_metrics.sentence_complexity, new_metrics.sentence_complexity, learning_rate
            ),
            vocabulary_sophistication=self._weighted_average(
                current_metrics.vocabulary_sophistication, new_metrics.vocabulary_sophistication, learning_rate
            ),
            sentiment_tendency=self._weighted_average(
                current_metrics.sentiment_tendency, new_metrics.sentiment_tendency, learning_rate
            ),
            directness_score=self._weighted_average(
                current_metrics.directness_score, new_metrics.directness_score, learning_rate
            ),
            avg_sentence_length=self._weighted_average(
                current_metrics.avg_sentence_length, new_metrics.avg_sentence_length, learning_rate
            ),
            avg_word_length=self._weighted_average(
                current_metrics.avg_word_length, new_metrics.avg_word_length, learning_rate
            ),
            exclamation_frequency=self._weighted_average(
                current_metrics.exclamation_frequency, new_metrics.exclamation_frequency, learning_rate
            ),
            question_frequency=self._weighted_average(
                current_metrics.question_frequency, new_metrics.question_frequency, learning_rate
            ),
            greeting_patterns=self._merge_patterns(
                current_metrics.greeting_patterns, new_metrics.greeting_patterns
            ),
            signature_patterns=self._merge_patterns(
                current_metrics.signature_patterns, new_metrics.signature_patterns
            ),
            common_phrases=self._merge_patterns(
                current_metrics.common_phrases, new_metrics.common_phrases
            )
        )
        
        # Update metadata
        profile.analyzed_emails += len(email_contents)
        profile.updated_at = datetime.now()
        profile.last_analysis = datetime.now()
        
        # Calculate confidence score based on number of emails analyzed
        profile.confidence_score = min(0.9, profile.analyzed_emails / 20.0)  # Max 0.9 confidence
        
        return profile
    
    def get_style_profile_as_text(self, profile: UserProfile) -> str:
        """Convert style profile to text description for AI consumption."""
        metrics = profile.style_metrics
        
        style_description = f"""
Writing Style Profile for {profile.email_address}:

Formality Level: {metrics.formality_score:.2f} ({'Very Formal' if metrics.formality_score > 0.7 else 'Formal' if metrics.formality_score > 0.4 else 'Casual' if metrics.formality_score > 0.2 else 'Very Casual'})
Sentence Complexity: {metrics.sentence_complexity:.2f} ({'Complex' if metrics.sentence_complexity > 0.7 else 'Moderate' if metrics.sentence_complexity > 0.4 else 'Simple'})
Vocabulary Level: {metrics.vocabulary_sophistication:.2f} ({'Sophisticated' if metrics.vocabulary_sophistication > 0.7 else 'Advanced' if metrics.vocabulary_sophistication > 0.4 else 'Basic'})
Communication Style: {metrics.directness_score:.2f} ({'Direct' if metrics.directness_score > 0.7 else 'Balanced' if metrics.directness_score > 0.4 else 'Indirect'})
Tone: {metrics.sentiment_tendency:.2f} ({'Very Positive' if metrics.sentiment_tendency > 0.3 else 'Positive' if metrics.sentiment_tendency > 0.1 else 'Neutral' if metrics.sentiment_tendency > -0.1 else 'Negative' if metrics.sentiment_tendency > -0.3 else 'Very Negative'})

Average sentence length: {metrics.avg_sentence_length:.1f} words
Average word length: {metrics.avg_word_length:.1f} characters
Exclamation usage: {metrics.exclamation_frequency:.2f} per sentence
Question usage: {metrics.question_frequency:.2f} per sentence

Common greeting patterns: {', '.join(metrics.greeting_patterns[:5])}
Common signature patterns: {', '.join(metrics.signature_patterns[:5])}
Frequently used phrases: {', '.join(metrics.common_phrases[:5])}

Profile confidence: {profile.confidence_score:.2f} (based on {profile.analyzed_emails} analyzed emails)
"""
        
        return style_description.strip()
    
    def load_profile(self, user_id: str) -> Optional[UserProfile]:
        """Load user profile from file."""
        profile_file = self.profile_dir / f"{user_id}.json"
        
        if not profile_file.exists():
            return None
        
        try:
            with open(profile_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Convert datetime strings back to datetime objects
            data['created_at'] = datetime.fromisoformat(data['created_at'])
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
            if data['last_analysis']:
                data['last_analysis'] = datetime.fromisoformat(data['last_analysis'])
            
            return UserProfile(**data)
            
        except Exception as e:
            self.console.print(f"[red]Error loading profile {user_id}: {e}[/red]")
            return None
    
    def save_profile(self, profile: UserProfile):
        """Save user profile to file."""
        profile_file = self.profile_dir / f"{profile.user_id}.json"
        
        try:
            # Convert datetime objects to strings for JSON serialization
            profile_data = profile.dict()
            profile_data['created_at'] = profile.created_at.isoformat()
            profile_data['updated_at'] = profile.updated_at.isoformat()
            if profile.last_analysis:
                profile_data['last_analysis'] = profile.last_analysis.isoformat()
            
            with open(profile_file, 'w', encoding='utf-8') as f:
                json.dump(profile_data, f, indent=2, default=str)
                
        except Exception as e:
            self.console.print(f"[red]Error saving profile {profile.user_id}: {e}[/red]")
    
    def list_profiles(self) -> List[str]:
        """List all available profile IDs."""
        profile_files = list(self.profile_dir.glob("*.json"))
        return [f.stem for f in profile_files]
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text for analysis."""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove email headers and signatures (basic extraction)
        lines = text.split('\n')
        body_lines = []
        
        for line in lines:
            line = line.strip()
            # Skip common signature lines
            if any(sig in line.lower() for sig in ['sent from', 'regards', 'sincerely', 'thanks', 'best']):
                break
            if line:
                body_lines.append(line)
        
        return ' '.join(body_lines)
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Simple sentence splitting - can be enhanced with NLTK
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text into words."""
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        return [word for word in words if len(word) > 1]
    
    def _calculate_formality(self, text: str, words: List[str]) -> float:
        """Calculate formality score based on indicators."""
        text_lower = text.lower()
        word_lower = [w.lower() for w in words]
        
        formal_count = sum(1 for indicator in self.formal_indicators if indicator in text_lower)
        informal_count = sum(1 for indicator in self.informal_indicators if indicator in text_lower)
        
        # Base score on word complexity
        base_score = textstat.flesch_kincaid_grade(text) / 12.0  # Normalize to 0-1
        
        # Adjust based on formal/informal indicators
        if formal_count + informal_count > 0:
            formal_ratio = formal_count / (formal_count + informal_count)
            return (base_score + formal_ratio) / 2
        
        return base_score
    
    def _calculate_complexity(self, sentences: List[str], words: List[str]) -> float:
        """Calculate sentence complexity score."""
        if not sentences or not words:
            return 0.5
        
        avg_sentence_length = len(words) / len(sentences)
        # Normalize to 0-1 scale (typical range is 10-30 words)
        normalized = min(1.0, avg_sentence_length / 25.0)
        
        return normalized
    
    def _calculate_vocabulary_sophistication(self, words: List[str]) -> float:
        """Calculate vocabulary sophistication score."""
        if not words:
            return 0.5
        
        # Simple metric based on average word length and rare words
        avg_length = sum(len(word) for word in words) / len(words)
        length_score = min(1.0, avg_length / 8.0)
        
        # Could be enhanced with word frequency analysis
        return length_score
    
    def _calculate_sentiment(self, words: List[str]) -> float:
        """Calculate sentiment tendency (-1 to 1)."""
        if not words:
            return 0.0
        
        positive_count = sum(1 for word in words if word in self.positive_words)
        negative_count = sum(1 for word in words if word in self.negative_words)
        
        total_sentiment_words = positive_count + negative_count
        if total_sentiment_words == 0:
            return 0.0
        
        return (positive_count - negative_count) / total_sentiment_words
    
    def _calculate_directness(self, text: str, sentences: List[str]) -> float:
        """Calculate communication directness score."""
        # Direct indicators: active voice, imperative mood
        direct_indicators = ['please', 'kindly', 'could you', 'would you', 'i need', 'we need']
        
        text_lower = text.lower()
        direct_count = sum(1 for indicator in direct_indicators if indicator in text_lower)
        
        # Normalize by number of sentences
        if sentences:
            return min(1.0, direct_count / len(sentences))
        
        return 0.5
    
    def _extract_greeting_patterns(self, email_text: str) -> List[str]:
        """Extract common greeting patterns from email."""
        lines = email_text.strip().split('\n')
        greetings = []
        
        greeting_patterns = [
            r'^(dear|hi|hello|hey|good morning|good afternoon|good evening)\s+[\w,\s]+,?$',
            r'^(mr|mrs|ms|dr)\.\s+[\w\s,]+$'
        ]
        
        for line in lines[:3]:  # Check first 3 lines
            line = line.strip()
            for pattern in greeting_patterns:
                if re.match(pattern, line, re.IGNORECASE):
                    greetings.append(line)
                    break
        
        return greetings[:3]  # Return top 3
    
    def _extract_signature_patterns(self, email_text: str) -> List[str]:
        """Extract common signature patterns from email."""
        lines = email_text.strip().split('\n')
        signatures = []
        
        # Look at last few lines
        for line in lines[-5:]:
            line = line.strip()
            if (any(sig in line.lower() for sig in ['regards', 'sincerely', 'thanks', 'best', 'sincerely']) or
                len(line.split()) <= 3):  # Short lines likely signatures
                signatures.append(line)
        
        return signatures[:3]
    
    def _extract_common_phrases(self, email_text: str) -> List[str]:
        """Extract commonly used phrases from email."""
        # Simple phrase extraction - could be enhanced
        sentences = self._split_sentences(email_text)
        phrases = []
        
        for sentence in sentences:
            words = sentence.split()
            # Look for common multi-word phrases
            for i in range(len(words) - 2):
                phrase = ' '.join(words[i:i+3])
                if len(phrase) > 10:  # Filter out short phrases
                    phrases.append(phrase)
        
        # Return most frequent phrases
        phrase_counts = {}
        for phrase in phrases:
            phrase_counts[phrase] = phrase_counts.get(phrase, 0) + 1
        
        sorted_phrases = sorted(phrase_counts.items(), key=lambda x: x[1], reverse=True)
        return [phrase for phrase, count in sorted_phrases[:5]]
    
    def _aggregate_metrics(self, metrics_list: List[StyleMetrics]) -> StyleMetrics:
        """Aggregate multiple metrics into a single profile."""
        if not metrics_list:
            raise ValueError("No metrics to aggregate")
        
        # Simple averaging for numeric values
        formality = statistics.mean(m.formality_score for m in metrics_list)
        complexity = statistics.mean(m.sentence_complexity for m in metrics_list)
        vocabulary = statistics.mean(m.vocabulary_sophistication for m in metrics_list)
        sentiment = statistics.mean(m.sentiment_tendency for m in metrics_list)
        directness = statistics.mean(m.directness_score for m in metrics_list)
        
        avg_sentence_len = statistics.mean(m.avg_sentence_length for m in metrics_list)
        avg_word_len = statistics.mean(m.avg_word_length for m in metrics_list)
        exclamation = statistics.mean(m.exclamation_frequency for m in metrics_list)
        question = statistics.mean(m.question_frequency for m in metrics_list)
        
        # Merge patterns (most common across all metrics)
        all_greetings = []
        all_signatures = []
        all_phrases = []
        
        for m in metrics_list:
            all_greetings.extend(m.greeting_patterns)
            all_signatures.extend(m.signature_patterns)
            all_phrases.extend(m.common_phrases)
        
        # Get most common patterns
        greeting_counts = {}
        for greeting in all_greetings:
            greeting_counts[greeting] = greeting_counts.get(greeting, 0) + 1
        
        signature_counts = {}
        for signature in all_signatures:
            signature_counts[signature] = signature_counts.get(signature, 0) + 1
        
        phrase_counts = {}
        for phrase in all_phrases:
            phrase_counts[phrase] = phrase_counts.get(phrase, 0) + 1
        
        common_greetings = [g for g, c in sorted(greeting_counts.items(), key=lambda x: x[1], reverse=True)[:3]]
        common_signatures = [s for s, c in sorted(signature_counts.items(), key=lambda x: x[1], reverse=True)[:3]]
        common_phrases = [p for p, c in sorted(phrase_counts.items(), key=lambda x: x[1], reverse=True)[:5]]
        
        return StyleMetrics(
            formality_score=formality,
            sentence_complexity=complexity,
            vocabulary_sophistication=vocabulary,
            sentiment_tendency=sentiment,
            directness_score=directness,
            avg_sentence_length=avg_sentence_len,
            avg_word_length=avg_word_len,
            exclamation_frequency=exclamation,
            question_frequency=question,
            greeting_patterns=common_greetings,
            signature_patterns=common_signatures,
            common_phrases=common_phrases
        )
    
    def _weighted_average(self, current: float, new: float, weight: float) -> float:
        """Calculate weighted average for learning."""
        return current * (1 - weight) + new * weight
    
    def _merge_patterns(self, current: List[str], new: List[str]) -> List[str]:
        """Merge pattern lists, keeping most common ones."""
        combined = current + new
        
        # Count frequencies and return most common
        pattern_counts = {}
        for pattern in combined:
            pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
        
        sorted_patterns = sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True)
        return [pattern for pattern, count in sorted_patterns[:5]]